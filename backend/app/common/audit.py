"""Audit log helper."""
from __future__ import annotations

from ..extensions import db
from ..models import AuditLog


def record(actor_id: int, action: str, *, group_id: int | None = None,
           target_type: str | None = None, target_id: int | None = None,
           payload: dict | None = None):
    db.session.add(
        AuditLog(
            actor_id=actor_id,
            group_id=group_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload=payload or {},
        )
    )
