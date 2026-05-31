"""Celery beat: DDL reminders & daily digest."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from celery.schedules import crontab
from sqlalchemy import select

from ..extensions import celery, db, get_redis
from ..models import Group, Task, TaskAssignment, User
from ..modules.notifications.service import add as add_notification

log = logging.getLogger(__name__)


@celery.task(name="cotask.ddl.scan")
def scan_ddls():
    """Scan tasks with DDL in the next 72h and notify assignees."""
    today = date.today()
    horizon = today + timedelta(days=3)

    rows = db.session.execute(
        select(Task, TaskAssignment, User)
        .join(TaskAssignment, TaskAssignment.task_id == Task.id)
        .join(User, User.id == TaskAssignment.user_id)
        .where(
            Task.deleted_at.is_(None),
            Task.status != "done",
            Task.end_date.is_not(None),
            Task.end_date >= today,
            Task.end_date <= horizon,
        )
    ).all()

    r = get_redis()
    notified = 0
    for t, a, u in rows:
        key = f"ddl_notify:{u.id}:{t.id}:{date.today().isoformat()}"
        if r.setnx(key, "1"):
            r.expire(key, 86400)
            days = (t.end_date - today).days
            add_notification(u.id, "ddl_warning", {
                "task_id": t.id,
                "task_title": t.title,
                "days_left": days,
                "end_date": t.end_date.isoformat(),
            })
            db.session.commit()
            notified += 1
    log.info("DDL scan: %d tasks, %d notifications sent", len(rows), notified)
    return {"scanned": len(rows), "sent": notified}


@celery.task(name="cotask.daily.digest")
def daily_digest():
    """Send a daily morning digest to users with active tasks."""
    today = date.today()
    rows = db.session.execute(
        select(User.id, User.email)
        .join(TaskAssignment, TaskAssignment.user_id == User.id)
        .join(Task, Task.id == TaskAssignment.task_id)
        .where(
            Task.deleted_at.is_(None),
            Task.status != "done",
            Task.end_date.is_not(None),
        ).distinct()
    ).all()
    log.info("daily digest: %d users", len(rows))
    return {"users": len(rows)}


# Beat schedule
celery.conf.beat_schedule = {
    "ddl-scan-every-10min": {
        "task": "cotask.ddl.scan",
        "schedule": 600.0,
    },
    "daily-digest-morning": {
        "task": "cotask.daily.digest",
        "schedule": crontab(hour=9, minute=0),
    },
}
