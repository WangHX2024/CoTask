"""Per-node subtree management permissions (in addition to group leader)."""
from __future__ import annotations

from sqlalchemy import select

from ..extensions import db
from ..models import GroupMember, Task, TaskClosure, TaskNodeManager
from .errors import Forbidden
from .permissions import get_group_role


def is_group_leader(user_id: int, group_id: int) -> bool:
    return get_group_role(user_id, group_id) == "leader"


def can_manage_task(user_id: int, group_id: int, task_id: int) -> bool:
    """Leader manages the whole group tree; others need an anchor manager row on an ancestor."""
    if is_group_leader(user_id, group_id):
        return True
    row = db.session.execute(
        select(TaskClosure.ancestor_id)
        .join(
            TaskNodeManager,
            (TaskNodeManager.task_id == TaskClosure.ancestor_id)
            & (TaskNodeManager.group_id == group_id)
            & (TaskNodeManager.user_id == user_id)
            & (TaskNodeManager.revoked_at.is_(None)),
        )
        .where(
            TaskClosure.descendant_id == task_id,
            TaskClosure.distance >= 0,
        )
        .limit(1)
    ).first()
    return row is not None


def assert_can_manage_task(user_id: int, group_id: int, task_id: int) -> None:
    if not can_manage_task(user_id, group_id, task_id):
        raise Forbidden("无权管理该节点及其子任务")


def assert_can_create_under_parent(user_id: int, group_id: int, parent_id: int | None) -> None:
    if parent_id is None:
        if not is_group_leader(user_id, group_id):
            raise Forbidden("仅组长可创建根级任务")
        return
    assert_can_manage_task(user_id, group_id, parent_id)


def managed_task_ids(user_id: int, group_id: int) -> set[int] | None:
    """Return None if user manages every task in the group (leader)."""
    if is_group_leader(user_id, group_id):
        return None
    rows = db.session.execute(
        select(TaskClosure.descendant_id)
        .join(
            TaskNodeManager,
            (TaskNodeManager.task_id == TaskClosure.ancestor_id)
            & (TaskNodeManager.group_id == group_id)
            & (TaskNodeManager.user_id == user_id)
            & (TaskNodeManager.revoked_at.is_(None)),
        )
        .join(Task, Task.id == TaskClosure.descendant_id)
        .where(Task.group_id == group_id, Task.deleted_at.is_(None))
    ).scalars().all()
    return set(rows)


def list_node_managers(group_id: int, task_id: int) -> list[dict]:
    rows = db.session.execute(
        select(TaskNodeManager).where(
            TaskNodeManager.group_id == group_id,
            TaskNodeManager.task_id == task_id,
            TaskNodeManager.revoked_at.is_(None),
        )
    ).scalars().all()
    return [
        {
            "user_id": r.user_id,
            "granted_by": r.granted_by,
            "granted_at": r.granted_at,
        }
        for r in rows
    ]


def sync_subtree_managers_from_assignees(
    actor_id: int,
    group_id: int,
    task_id: int,
    assignee_ids: list[int],
) -> None:
    """Assignees on a node are its subtree managers (anchor = this task_id)."""
    current_rows = db.session.execute(
        select(TaskNodeManager).where(
            TaskNodeManager.group_id == group_id,
            TaskNodeManager.task_id == task_id,
            TaskNodeManager.revoked_at.is_(None),
        )
    ).scalars().all()
    current_ids = {r.user_id for r in current_rows}
    target_ids = set(assignee_ids)
    for uid in target_ids - current_ids:
        _grant_node_manager_row(actor_id, group_id, task_id, uid)
    for uid in current_ids - target_ids:
        _revoke_node_manager_row(group_id, task_id, uid)


def _grant_node_manager_row(
    actor_id: int, group_id: int, task_id: int, target_user_id: int
) -> TaskNodeManager:
    member = db.session.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == target_user_id,
        )
    ).scalar_one_or_none()
    if not member:
        raise Forbidden("目标用户不是小组成员")
    from .datetime_util import utc_now

    row = db.session.execute(
        select(TaskNodeManager).where(
            TaskNodeManager.group_id == group_id,
            TaskNodeManager.task_id == task_id,
            TaskNodeManager.user_id == target_user_id,
        )
    ).scalar_one_or_none()
    if row:
        if row.revoked_at is None:
            return row
        row.revoked_at = None
        row.granted_by = actor_id
        row.granted_at = utc_now()
        db.session.flush()
        return row

    row = TaskNodeManager(
        group_id=group_id,
        task_id=task_id,
        user_id=target_user_id,
        granted_by=actor_id,
        granted_at=utc_now(),
    )
    db.session.add(row)
    db.session.flush()
    return row


def _revoke_node_manager_row(group_id: int, task_id: int, target_user_id: int) -> None:
    from .datetime_util import utc_now

    row = db.session.execute(
        select(TaskNodeManager).where(
            TaskNodeManager.group_id == group_id,
            TaskNodeManager.task_id == task_id,
            TaskNodeManager.user_id == target_user_id,
            TaskNodeManager.revoked_at.is_(None),
        )
    ).scalar_one_or_none()
    if row:
        row.revoked_at = utc_now()


def grant_node_manager(
    actor_id: int, group_id: int, task_id: int, target_user_id: int
) -> dict:
    assert_can_manage_task(actor_id, group_id, task_id)
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id or t.deleted_at:
        raise Forbidden("节点无效")
    row = _grant_node_manager_row(actor_id, group_id, task_id, target_user_id)
    return {
        "user_id": target_user_id,
        "granted_by": row.granted_by,
        "granted_at": row.granted_at,
    }


def revoke_node_manager(
    actor_id: int, group_id: int, task_id: int, target_user_id: int
) -> None:
    assert_can_manage_task(actor_id, group_id, task_id)
    _revoke_node_manager_row(group_id, task_id, target_user_id)
