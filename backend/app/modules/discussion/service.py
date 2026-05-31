from __future__ import annotations

from sqlalchemy import select

from ...common.datetime_util import to_api_datetime
from ...common.errors import BadRequest, NotFound
from ...common.tx import tx
from ...extensions import db
from ...models import (
    DiscussionChannel,
    DiscussionMessage,
    GroupMember,
    Task,
    User,
)
from ..notifications.service import push_ws

GROUP_CHANNEL_NAME = "全员"


def _serialize_channel(c: DiscussionChannel) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "task_id": c.task_id,
        "created_by": c.created_by,
        "created_at": to_api_datetime(c.created_at),
    }


def build_task_channel_name(group_id: int, task_id: int) -> str:
    """Task path only, e.g. 读书报告 / 讲稿撰写 (no course or group name)."""
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id:
        return "任务讨论"
    parts: list[str] = []
    if t.path:
        for seg in t.path.strip("/").split("/"):
            if not seg.isdigit():
                continue
            node = db.session.get(Task, int(seg))
            if node and node.title:
                title = node.title.strip()
                if title and (not parts or parts[-1] != title):
                    parts.append(title)
    elif t.title:
        parts.append(t.title.strip())
    name = " / ".join(parts) if parts else (t.title or "任务讨论")
    return name[:256]


def _ensure_group_channel(uid: int, gid: int) -> DiscussionChannel | None:
    row = db.session.execute(
        select(DiscussionChannel).where(
            DiscussionChannel.group_id == gid,
            DiscussionChannel.task_id.is_(None),
            DiscussionChannel.name == GROUP_CHANNEL_NAME,
        )
    ).scalar_one_or_none()
    if row:
        return row
    with tx() as s:
        c = DiscussionChannel(
            group_id=gid,
            name=GROUP_CHANNEL_NAME,
            task_id=None,
            created_by=uid,
        )
        s.add(c)
        s.flush()
    return c


def list_channels(gid: int, uid: int) -> list[dict]:
    rows = db.session.execute(
        select(DiscussionChannel)
        .where(DiscussionChannel.group_id == gid)
        .order_by(
            DiscussionChannel.task_id.is_(None).desc(),
            DiscussionChannel.created_at.asc(),
        )
    ).scalars().all()
    if not any(c.task_id is None and c.name == GROUP_CHANNEL_NAME for c in rows):
        _ensure_group_channel(uid, gid)
        rows = db.session.execute(
            select(DiscussionChannel)
            .where(DiscussionChannel.group_id == gid)
            .order_by(
                DiscussionChannel.task_id.is_(None).desc(),
                DiscussionChannel.created_at.asc(),
            )
        ).scalars().all()
    return [_serialize_channel(c) for c in rows]


def create_channel(uid: int, gid: int, name: str, task_id: int | None = None) -> dict:
    name = (name or "").strip()
    if task_id:
        pass
    elif not name:
        raise BadRequest("MISSING_NAME", "需指定频道名称")
    if task_id:
        t = db.session.get(Task, task_id)
        if not t or t.group_id != gid or t.deleted_at:
            raise NotFound("task")
        existing = db.session.execute(
            select(DiscussionChannel).where(
                DiscussionChannel.group_id == gid,
                DiscussionChannel.task_id == task_id,
            )
        ).scalar_one_or_none()
        if existing:
            return _serialize_channel(existing)
        name = name or build_task_channel_name(gid, task_id)
    if len(name) > 256:
        name = name[:253] + "..."
    with tx() as s:
        c = DiscussionChannel(
            group_id=gid,
            name=name,
            task_id=task_id,
            created_by=uid,
        )
        s.add(c)
        s.flush()
    return _serialize_channel(c)


def get_or_create_task_channel(uid: int, gid: int, task_id: int) -> dict:
    t = db.session.get(Task, task_id)
    if not t or t.group_id != gid or t.deleted_at:
        raise NotFound("task")
    existing = db.session.execute(
        select(DiscussionChannel).where(
            DiscussionChannel.group_id == gid,
            DiscussionChannel.task_id == task_id,
        )
    ).scalar_one_or_none()
    if existing:
        return _serialize_channel(existing)
    return create_channel(uid, gid, "", task_id=task_id)


def channel_message_count(channel_id: int) -> int:
    from sqlalchemy import func

    return db.session.execute(
        select(func.count())
        .select_from(DiscussionMessage)
        .where(
            DiscussionMessage.channel_id == channel_id,
            DiscussionMessage.deleted_at.is_(None),
        )
    ).scalar_one()


def post_message(uid: int, gid: int, data: dict) -> dict:
    channel_id = data.get("channel_id")
    task_id = data.get("task_id")
    if not channel_id and not task_id:
        raise BadRequest("MISSING_TARGET", "需指定频道或任务")
    if channel_id:
        ch = db.session.get(DiscussionChannel, channel_id)
        if not ch or ch.group_id != gid:
            raise NotFound("channel")
    if task_id:
        t = db.session.get(Task, task_id)
        if not t or t.group_id != gid:
            raise NotFound("task")
    with tx() as s:
        m = DiscussionMessage(
            channel_id=channel_id,
            task_id=task_id,
            author_id=uid,
            body=data["body"],
            anon=False,
            quote_id=data.get("quote_id"),
        )
        s.add(m)
        s.flush()
    payload = _serialize(m)
    push_ws(gid, "discussion.message", payload)
    return payload


def list_messages(uid: int, gid: int, channel_id: int | None = None, task_id: int | None = None,
                  limit: int = 50, before_id: int | None = None) -> list[dict]:
    q = select(DiscussionMessage).where(DiscussionMessage.deleted_at.is_(None))
    if channel_id:
        q = q.where(DiscussionMessage.channel_id == channel_id)
    if task_id:
        q = q.where(DiscussionMessage.task_id == task_id)
    if before_id:
        q = q.where(DiscussionMessage.id < before_id)
    q = q.order_by(DiscussionMessage.id.desc()).limit(min(limit, 200))
    rows = db.session.execute(q).scalars().all()
    return [_serialize(m) for m in reversed(rows)]


def _serialize(m: DiscussionMessage) -> dict:
    if m.anon:
        mem = None
        if m.channel_id:
            ch = db.session.get(DiscussionChannel, m.channel_id)
            if ch:
                mem = db.session.execute(
                    select(GroupMember).where(
                        GroupMember.group_id == ch.group_id,
                        GroupMember.user_id == m.author_id,
                    )
                ).scalar_one_or_none()
        elif m.task_id:
            t = db.session.get(Task, m.task_id)
            if t:
                mem = db.session.execute(
                    select(GroupMember).where(
                        GroupMember.group_id == t.group_id,
                        GroupMember.user_id == m.author_id,
                    )
                ).scalar_one_or_none()
        anon_id = mem.anon_id if mem else "X1X1"
        author_name = f"匿名同学#{anon_id}"
        avatar = ""
        author_id = 0
    else:
        u = db.session.get(User, m.author_id)
        author_name = u.name if u else "用户"
        avatar = u.avatar_url if u else ""
        author_id = m.author_id
    return {
        "id": m.id,
        "channel_id": m.channel_id,
        "task_id": m.task_id,
        "body": m.body,
        "author_id": author_id,
        "author_name": author_name,
        "author_avatar": avatar,
        "anon": m.anon,
        "quote_id": m.quote_id,
        "created_at": to_api_datetime(m.created_at),
    }
