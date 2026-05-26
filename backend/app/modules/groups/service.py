from __future__ import annotations

from sqlalchemy import func, select

from ...common import audit
from ...common.errors import BadRequest, Conflict, Forbidden, NotFound
from ...common.permissions import invalidate_role_cache
from ...common.tx import tx
from ...common.utils import gen_anon_id, gen_invite_code
from ...extensions import db
from ...models import Group, GroupMember, Task, User


def _ensure_unique_invite_code() -> str:
    for _ in range(20):
        code = gen_invite_code()
        if not db.session.execute(
            db.select(Group.id).where(Group.invite_code == code)
        ).scalar_one_or_none():
            return code
    raise BadRequest("INTERNAL", "邀请码生成失败")


def create_group(uid: int, payload: dict) -> Group:
    with tx() as s:
        g = Group(
            course_name=payload["course_name"],
            name=payload["name"],
            description=payload.get("description"),
            invite_code=_ensure_unique_invite_code(),
            created_by=uid,
        )
        s.add(g)
        s.flush()
        s.add(GroupMember(group_id=g.id, user_id=uid, role="leader", anon_id=gen_anon_id()))
        audit.record(uid, "group.create", group_id=g.id, target_type="group", target_id=g.id,
                     payload={"name": g.name})
    invalidate_role_cache(uid, g.id)
    return g


def list_my_groups(uid: int):
    rows = db.session.execute(
        db.select(Group, GroupMember.role)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == uid, Group.status != "dissolved")
        .order_by(Group.created_at.desc())
    ).all()
    out = []
    for g, role in rows:
        out.append(_serialize_group(g, role))
    return out


def _serialize_group(g: Group, role: str) -> dict:
    member_count = db.session.execute(
        db.select(func.count()).select_from(GroupMember).where(GroupMember.group_id == g.id)
    ).scalar_one()
    progress = db.session.execute(
        db.select(func.avg(Task.progress)).where(
            Task.group_id == g.id, Task.is_leaf.is_(True), Task.deleted_at.is_(None)
        )
    ).scalar_one() or 0
    return {
        "id": g.id,
        "course_name": g.course_name,
        "name": g.name,
        "invite_code": g.invite_code if role == "leader" else None,
        "status": g.status,
        "description": g.description,
        "created_by": g.created_by,
        "created_at": g.created_at,
        "role": role,
        "member_count": int(member_count),
        "progress": int(progress),
    }


def get_group(uid: int, gid: int) -> dict:
    g = db.session.get(Group, gid)
    if not g or g.status == "dissolved":
        raise NotFound("group")
    m = db.session.execute(
        db.select(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == uid)
    ).scalar_one_or_none()
    if not m:
        raise Forbidden("非小组成员")
    return _serialize_group(g, m.role)


def update_group(uid: int, gid: int, data: dict) -> dict:
    g = db.session.get(Group, gid)
    if not g:
        raise NotFound("group")
    with tx():
        for k, v in data.items():
            if v is not None:
                setattr(g, k, v)
        audit.record(uid, "group.update", group_id=gid, target_type="group", target_id=gid, payload=data)
    role = db.session.execute(
        db.select(GroupMember.role).where(GroupMember.group_id == gid, GroupMember.user_id == uid)
    ).scalar_one()
    return _serialize_group(g, role)


def join_group(uid: int, invite_code: str) -> dict:
    g = db.session.execute(db.select(Group).where(Group.invite_code == invite_code)).scalar_one_or_none()
    if not g:
        raise NotFound(message="邀请码不正确，请向组长核对后重试")
    if g.status != "active":
        raise BadRequest("GROUP_INACTIVE", "该小组已暂停或解散，暂时无法加入")
    existing = db.session.execute(
        db.select(GroupMember).where(GroupMember.group_id == g.id, GroupMember.user_id == uid)
    ).scalar_one_or_none()
    if existing:
        raise Conflict("ALREADY_MEMBER", "已是小组成员")
    with tx() as s:
        s.add(GroupMember(group_id=g.id, user_id=uid, role="member", anon_id=gen_anon_id()))
        audit.record(uid, "group.join", group_id=g.id, target_type="group", target_id=g.id)
    invalidate_role_cache(uid, g.id)
    return _serialize_group(g, "member")


def list_members(gid: int):
    rows = db.session.execute(
        db.select(GroupMember, User)
        .join(User, User.id == GroupMember.user_id)
        .where(GroupMember.group_id == gid)
        .order_by(GroupMember.role.desc(), GroupMember.joined_at.asc())
    ).all()
    out = []
    for m, u in rows:
        out.append({
            "user_id": u.id,
            "name": u.name,
            "avatar_url": u.avatar_url,
            "role": m.role,
            "anon_id": m.anon_id,
            "joined_at": m.joined_at,
            "contribution": u.contribution,
            "skills": [s.skill for s in u.skills],
        })
    return out


def kick_member(actor_id: int, gid: int, target_uid: int):
    if actor_id == target_uid:
        raise BadRequest("CANNOT_KICK_SELF", "不能踢出自己")
    m = db.session.execute(
        db.select(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == target_uid)
    ).scalar_one_or_none()
    if not m:
        raise NotFound("member")
    if m.role == "leader":
        raise BadRequest("CANNOT_KICK_LEADER", "无法踢出组长，请先转让")
    with tx() as s:
        s.delete(m)
        audit.record(actor_id, "group.kick", group_id=gid, target_type="user", target_id=target_uid)
    invalidate_role_cache(target_uid, gid)


def transfer_leader(actor_id: int, gid: int, target_uid: int):
    target = db.session.execute(
        db.select(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == target_uid)
    ).scalar_one_or_none()
    if not target:
        raise NotFound("target")
    actor = db.session.execute(
        db.select(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == actor_id)
    ).scalar_one()
    with tx():
        actor.role = "member"
        target.role = "leader"
        audit.record(actor_id, "group.transfer", group_id=gid, target_type="user", target_id=target_uid)
    invalidate_role_cache(actor_id, gid)
    invalidate_role_cache(target_uid, gid)


def leave_group(uid: int, gid: int):
    m = db.session.execute(
        db.select(GroupMember).where(GroupMember.group_id == gid, GroupMember.user_id == uid)
    ).scalar_one_or_none()
    if not m:
        raise NotFound("membership")
    if m.role == "leader":
        raise BadRequest("LEADER_LEAVE", "组长须先转让")
    with tx() as s:
        s.delete(m)
        audit.record(uid, "group.leave", group_id=gid)
    invalidate_role_cache(uid, gid)


def dissolve_group(uid: int, gid: int, confirm_name: str):
    g = db.session.get(Group, gid)
    if not g:
        raise NotFound("group")
    if g.name != confirm_name:
        raise BadRequest("CONFIRM_MISMATCH", "请输入完整小组名以确认解散")
    with tx():
        g.status = "dissolved"
        audit.record(uid, "group.dissolve", group_id=gid, target_type="group", target_id=gid)
