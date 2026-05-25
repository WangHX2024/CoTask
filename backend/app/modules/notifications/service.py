"""Notifications and WebSocket fan-out via Redis pub/sub."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from ...common.tx import tx
from ...extensions import db, get_redis
from ...models import GroupMember, Notification

log = logging.getLogger(__name__)


# ---- WS pub/sub channels ----
# - group:<gid>      group-scoped broadcast
# - user:<uid>       user-scoped (private)


def _publish(channel: str, event: str, data: dict):
    try:
        get_redis().publish(channel, json.dumps({"event": event, "data": data},
                                                 default=_json_default))
    except Exception:
        log.exception("WS publish failed")


def _json_default(o: Any):
    if isinstance(o, (datetime,)):
        return o.isoformat()
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return str(o)


def push_ws(group_id: int, event: str, payload: dict):
    _publish(f"group:{group_id}", event, payload)


def push_user(user_id: int, event: str, payload: dict):
    _publish(f"user:{user_id}", event, payload)


def add(user_id: int, ntype: str, payload: dict):
    db.session.add(Notification(user_id=user_id, type=ntype, payload=payload))
    push_user(user_id, "notification.new", {"type": ntype, "payload": payload})


def list_notifications(uid: int, only_unread: bool = False, limit: int = 50):
    q = select(Notification).where(Notification.user_id == uid)
    if only_unread:
        q = q.where(Notification.read_at.is_(None))
    q = q.order_by(Notification.created_at.desc()).limit(limit)
    return db.session.execute(q).scalars().all()


def mark_read(uid: int, ids: list[int] | None = None):
    with tx() as s:
        q = db.update(Notification).where(
            Notification.user_id == uid, Notification.read_at.is_(None)
        )
        if ids:
            q = q.where(Notification.id.in_(ids))
        s.execute(q.values(read_at=datetime.utcnow()))


def unread_count(uid: int) -> int:
    from sqlalchemy import func
    return int(db.session.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == uid, Notification.read_at.is_(None)
        )
    ).scalar_one())


def user_groups(uid: int) -> list[int]:
    return [
        r.group_id
        for r in db.session.execute(
            select(GroupMember).where(GroupMember.user_id == uid)
        ).scalars().all()
    ]
