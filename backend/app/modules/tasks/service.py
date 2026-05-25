from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select

from ...common import audit
from ...common.errors import BadRequest, Forbidden, NotFound
from ...common.tx import tx
from ...extensions import db, get_redis
from ...models import (
    GroupMember,
    Notification,
    Task,
    TaskAssignment,
    TaskInspirationRef,
    User,
)
from ..notifications.service import push_ws
from ..tree.service import _ensure_member, _recompute_ancestors_progress
from ..users.service import adjust_contribution


def _get_task(group_id: int, task_id: int) -> Task:
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id or t.deleted_at:
        raise NotFound("task")
    return t


def get_detail(group_id: int, task_id: int) -> dict:
    t = _get_task(group_id, task_id)
    assignees = [
        r.user_id for r in db.session.execute(
            select(TaskAssignment).where(TaskAssignment.task_id == task_id)
        ).scalars().all()
    ]
    from ...models import TaskDependency
    deps = [
        r.depends_on for r in db.session.execute(
            select(TaskDependency).where(TaskDependency.task_id == task_id)
        ).scalars().all()
    ]
    inspos = [
        r.post_id for r in db.session.execute(
            select(TaskInspirationRef).where(TaskInspirationRef.task_id == task_id)
        ).scalars().all()
    ]
    return {
        "id": t.id, "group_id": t.group_id, "parent_id": t.parent_id,
        "title": t.title, "description": t.description or "",
        "is_leaf": t.is_leaf, "refined": t.refined,
        "start_date": t.start_date, "end_date": t.end_date,
        "status": t.status, "progress": t.progress,
        "assignees": assignees, "dependencies": deps,
        "inspiration_post_ids": inspos,
        "path": t.path, "depth": t.depth, "version": t.version,
    }


def change_status(actor_id: int, group_id: int, task_id: int, new_status: str, role: str):
    t = _get_task(group_id, task_id)
    if not t.is_leaf:
        raise BadRequest("NOT_LEAF", "仅原子任务可推进状态")
    if role != "leader":
        assigned = db.session.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task_id, TaskAssignment.user_id == actor_id
            )
        ).scalar_one_or_none()
        if not assigned:
            raise Forbidden("仅负责人或组长可推进")
    old_status = t.status
    with tx():
        t.status = new_status
        t.version += 1
        if new_status == "done":
            t.progress = 100
            # contribution: on-time = +10, late = -5
            if t.end_date and date.today() <= t.end_date:
                # +10 per assignee
                for r in db.session.execute(
                    select(TaskAssignment).where(TaskAssignment.task_id == task_id)
                ).scalars().all():
                    adjust_contribution(r.user_id, 10, "task_done_on_time",
                                        "task", task_id)
            else:
                for r in db.session.execute(
                    select(TaskAssignment).where(TaskAssignment.task_id == task_id)
                ).scalars().all():
                    adjust_contribution(r.user_id, -5, "task_done_late",
                                        "task", task_id)
        elif new_status == "todo":
            t.progress = 0
        elif new_status == "in_progress" and t.progress == 0:
            t.progress = 30
        _recompute_ancestors_progress(task_id)
        audit.record(actor_id, "task.status",
                     group_id=group_id, target_type="task", target_id=task_id,
                     payload={"from": old_status, "to": new_status})
    push_ws(group_id, "task.status_changed", {
        "task_id": task_id, "status": new_status, "by": actor_id,
    })
    return get_detail(group_id, task_id)


def assign(actor_id: int, group_id: int, task_id: int, users: list[int]):
    t = _get_task(group_id, task_id)
    _ensure_member(group_id, users)
    with tx() as s:
        s.execute(db.delete(TaskAssignment).where(TaskAssignment.task_id == task_id))
        for uid in users:
            s.add(TaskAssignment(task_id=task_id, user_id=uid))
        t.version += 1
        audit.record(actor_id, "task.assign", group_id=group_id, target_type="task",
                     target_id=task_id, payload={"users": users})
    for uid in users:
        push_ws(group_id, "task.assigned", {"task_id": task_id, "user_id": uid})
        _add_notification(uid, "assigned", {"task_id": task_id, "title": t.title})
    return get_detail(group_id, task_id)


def nudge(actor_id: int, group_id: int, task_id: int, message: str):
    t = _get_task(group_id, task_id)
    if not t.is_leaf:
        raise BadRequest("NOT_LEAF", "仅原子任务可催办")
    assignees = [
        r.user_id for r in db.session.execute(
            select(TaskAssignment).where(TaskAssignment.task_id == task_id)
        ).scalars().all()
    ]
    r = get_redis()
    sent = 0
    for uid in assignees:
        if uid == actor_id:
            continue
        key = f"nudge:{actor_id}:{uid}:{task_id}"
        if r.setnx(key, "1"):
            r.expire(key, 86400)
            _add_notification(uid, "nudge", {
                "task_id": task_id,
                "task_title": t.title,
                "from_user_id": actor_id,
                "message": message,
            })
            push_ws(group_id, "task.nudged", {
                "task_id": task_id, "from_user_id": actor_id,
                "to_user_id": uid, "message": message,
            })
            sent += 1
    if sent == 0:
        raise BadRequest("NUDGE_COOLDOWN", "24小时内已催办过")
    audit.record(actor_id, "task.nudge", group_id=group_id, target_type="task", target_id=task_id)


def _add_notification(user_id: int, ntype: str, payload: dict):
    db.session.add(Notification(user_id=user_id, type=ntype, payload=payload))


def attach_inspiration(actor_id: int, group_id: int, task_id: int, post_id: int, source: str = "manual"):
    t = _get_task(group_id, task_id)
    existing = db.session.execute(
        select(TaskInspirationRef).where(
            TaskInspirationRef.task_id == task_id,
            TaskInspirationRef.post_id == post_id,
        )
    ).scalar_one_or_none()
    if existing:
        return
    with tx() as s:
        s.add(TaskInspirationRef(task_id=task_id, post_id=post_id, source=source))


def detach_inspiration(actor_id: int, group_id: int, task_id: int, post_id: int):
    _get_task(group_id, task_id)
    with tx() as s:
        s.execute(
            db.delete(TaskInspirationRef).where(
                TaskInspirationRef.task_id == task_id,
                TaskInspirationRef.post_id == post_id,
            )
        )
