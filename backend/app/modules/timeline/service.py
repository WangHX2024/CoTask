from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select

from ...extensions import db
from ...models import (
    GroupMember,
    Task,
    TaskAssignment,
    TaskDependency,
    User,
)


def _window(view: str, start: date | None) -> tuple[date, date]:
    today = date.today()
    if not start:
        start = today
    if view == "month":
        # align to first day of month
        s = start.replace(day=1)
        # next month minus 1 day
        next_m = (s.replace(day=28) + timedelta(days=4)).replace(day=1)
        return s, next_m - timedelta(days=1)
    # week (default): monday-sunday containing `start`
    s = start - timedelta(days=start.weekday())
    return s, s + timedelta(days=6)


def _title_by_id_for_tasks(task_rows: list) -> dict[int, str]:
    ids: set[int] = set()
    for t, _, _ in task_rows:
        if t.path:
            for seg in t.path.strip("/").split("/"):
                if seg.isdigit():
                    ids.add(int(seg))
    if not ids:
        return {}
    return {
        row[0]: row[1]
        for row in db.session.execute(
            select(Task.id, Task.title).where(
                Task.id.in_(ids),
                Task.deleted_at.is_(None),
            )
        ).all()
    }


def _title_path(task: Task, title_by_id: dict[int, str]) -> str:
    if not task.path:
        return task.title
    names: list[str] = []
    for seg in task.path.strip("/").split("/"):
        if seg.isdigit():
            names.append(title_by_id.get(int(seg), "…"))
    return " / ".join(names) if names else task.title


def get_timeline(group_id: int, view: str, start: date | None) -> dict:
    s, e = _window(view, start)
    members = db.session.execute(
        select(GroupMember, User)
        .join(User, User.id == GroupMember.user_id)
        .where(GroupMember.group_id == group_id)
    ).all()

    tasks = db.session.execute(
        select(Task, TaskAssignment, User)
        .join(TaskAssignment, TaskAssignment.task_id == Task.id)
        .join(User, User.id == TaskAssignment.user_id)
        .where(
            Task.group_id == group_id,
            Task.deleted_at.is_(None),
            Task.start_date.isnot(None),
            Task.end_date.isnot(None),
            Task.start_date <= e,
            Task.end_date >= s,
        )
    ).all()

    deps_map: dict[int, list[int]] = {}
    task_ids = list({row[0].id for row in tasks})
    if task_ids:
        for d in db.session.execute(
            select(TaskDependency).where(TaskDependency.task_id.in_(task_ids))
        ).scalars().all():
            deps_map.setdefault(d.task_id, []).append(d.depends_on)

    title_by_id = _title_by_id_for_tasks(tasks)

    today = date.today()
    rows_by_uid: dict[int, dict] = {}
    for m, u in members:
        rows_by_uid[u.id] = {
            "user_id": u.id,
            "name": u.name,
            "avatar_url": u.avatar_url,
            "role": m.role,
            "blocks": [],
        }
    for t, a, u in tasks:
        urgent = (
            t.end_date is not None
            and t.status != "done"
            and 0 <= (t.end_date - today).days <= 3
        )
        block = {
            "task_id": t.id,
            "title": t.title,
            "title_path": _title_path(t, title_by_id),
            "user_id": u.id,
            "user_name": u.name,
            "user_avatar": u.avatar_url,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "status": t.status,
            "progress": t.progress,
            "urgent": urgent,
            "dependencies": deps_map.get(t.id, []),
        }
        if u.id in rows_by_uid:
            rows_by_uid[u.id]["blocks"].append(block)

    rows = sorted(
        rows_by_uid.values(),
        key=lambda r: (0 if r["role"] == "leader" else 1, r["user_id"]),
    )
    return {"view": view, "start": s, "end": e, "rows": rows}
