from __future__ import annotations

from sqlalchemy import select

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


def list_channels(gid: int) -> list[dict]:
    rows = db.session.execute(
        select(DiscussionChannel).where(DiscussionChannel.group_id == gid)
        .order_by(DiscussionChannel.created_at.asc())
    ).scalars().all()
    if not rows:
        # auto-create #全员 channel
        return []
    return [
        {"id": c.id, "name": c.name, "created_by": c.created_by, "created_at": c.created_at}
        for c in rows
    ]


def create_channel(uid: int, gid: int, name: str) -> dict:
    with tx() as s:
        c = DiscussionChannel(group_id=gid, name=name, created_by=uid)
        s.add(c)
        s.flush()
    return {"id": c.id, "name": c.name, "created_by": c.created_by, "created_at": c.created_at}


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
            anon=bool(data.get("anon")),
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
        # find anon_id in group_members for this user
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
        "created_at": m.created_at,
    }
