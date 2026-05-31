"""Project tree service.

Storage strategy: adjacency list (parent_id) + materialized path + closure table.
- parent_id: source of truth for parent/child
- path / depth: used for ordered renders ("/3/9/12/")
- task_closure: O(1) ancestor/descendant queries
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Iterable

from sqlalchemy import func, select

from ...common import audit
from ...common.errors import BadRequest, Conflict, Forbidden, NotFound
from ...common.task_permissions import (
    assert_can_create_under_parent,
    assert_can_manage_task,
    can_manage_task,
    grant_node_manager,
    list_node_managers,
    managed_task_ids,
    revoke_node_manager,
    sync_subtree_managers_from_assignees,
)
from ...common.tx import tx
from ..notifications.service import push_ws
from ...extensions import db
from ...models import (
    GroupMember,
    Task,
    TaskAssignment,
    TaskClosure,
    TaskDependency,
)

log = logging.getLogger(__name__)


# ---------- helpers ----------


def _path_of(parent: Task | None, new_id: int) -> str:
    base = parent.path if parent else "/"
    return f"{base}{new_id}/"


def _all_descendants(task_id: int) -> list[int]:
    return [
        row.descendant_id
        for row in db.session.execute(
            select(TaskClosure).where(TaskClosure.ancestor_id == task_id)
        )
        .scalars()
        .all()
    ]


def _ensure_member(group_id: int, user_ids: Iterable[int]):
    if not user_ids:
        return
    rows = db.session.execute(
        select(GroupMember.user_id).where(
            GroupMember.group_id == group_id, GroupMember.user_id.in_(list(user_ids))
        )
    ).all()
    valid = {r[0] for r in rows}
    invalid = set(user_ids) - valid
    if invalid:
        raise BadRequest("BAD_ASSIGNEE", f"用户不在小组内: {invalid}")


def _insert_closure_for_new(task_id: int, parent_id: int | None):
    """Insert closure rows for a newly created node."""
    rows = [{"ancestor_id": task_id, "descendant_id": task_id, "distance": 0}]
    if parent_id is not None:
        parent_ancestors = db.session.execute(
            select(TaskClosure).where(TaskClosure.descendant_id == parent_id)
        ).scalars().all()
        for r in parent_ancestors:
            rows.append({
                "ancestor_id": r.ancestor_id,
                "descendant_id": task_id,
                "distance": r.distance + 1,
            })
    db.session.execute(db.insert(TaskClosure), rows)


def _detach_subtree_closure(root_id: int):
    """Remove all (ancestor != self) → descendant edges for a subtree."""
    desc_ids = _all_descendants(root_id)
    if not desc_ids:
        return
    db.session.execute(
        db.delete(TaskClosure).where(
            TaskClosure.descendant_id.in_(desc_ids),
            TaskClosure.ancestor_id.notin_(desc_ids),
        )
    )


def _attach_subtree_closure(root_id: int, new_parent_id: int | None):
    """Re-attach: for each descendant of root, add closure rows from all new ancestors."""
    if new_parent_id is None:
        return
    desc_rows = db.session.execute(
        select(TaskClosure).where(TaskClosure.ancestor_id == root_id)
    ).scalars().all()
    parent_anc = db.session.execute(
        select(TaskClosure).where(TaskClosure.descendant_id == new_parent_id)
    ).scalars().all()
    rows = []
    for p in parent_anc:
        for d in desc_rows:
            rows.append({
                "ancestor_id": p.ancestor_id,
                "descendant_id": d.descendant_id,
                "distance": p.distance + 1 + d.distance,
            })
    if rows:
        db.session.execute(db.insert(TaskClosure), rows)


def _rebuild_paths(root_id: int):
    """After a move, rewrite path/depth for the whole subtree."""
    root = db.session.get(Task, root_id)
    if not root:
        return
    if root.parent_id is None:
        root.path = f"/{root.id}/"
        root.depth = 0
    else:
        parent = db.session.get(Task, root.parent_id)
        root.path = f"{parent.path}{root.id}/"
        root.depth = parent.depth + 1
    # BFS through descendants
    queue = [root.id]
    while queue:
        cur_id = queue.pop(0)
        cur = db.session.get(Task, cur_id)
        children = db.session.execute(
            select(Task).where(Task.parent_id == cur_id, Task.deleted_at.is_(None))
        ).scalars().all()
        for c in children:
            c.path = f"{cur.path}{c.id}/"
            c.depth = cur.depth + 1
            queue.append(c.id)


def _bump_versions(task_ids: list[int]):
    if not task_ids:
        return
    db.session.execute(
        db.update(Task).where(Task.id.in_(task_ids)).values(version=Task.version + 1)
    )


# ---------- progress aggregation ----------

TASK_STATUS = frozenset({"todo", "in_progress", "done", "blocked"})


def _clamp_progress_for_status(progress: int, status: str) -> int:
    """Progress 100 is reserved for status=done."""
    progress = max(0, min(100, int(progress or 0)))
    if status == "done":
        return 100
    if status in ("todo", "blocked"):
        return 0
    # in_progress
    if progress >= 100:
        return 99
    return progress


def _progress_for_status(status: str, current: int = 0) -> int:
    """Map a manual status change to a progress percentage."""
    if status == "done":
        return 100
    if status == "todo":
        return 0
    if status == "blocked":
        return 0
    if status == "in_progress":
        p = int(current or 0)
        if p >= 100:
            return 30
        if p > 0:
            return p
        return 30
    return max(0, min(100, int(current or 0)))


def _aggregate_from_children(children: list[Task]) -> tuple[int, str]:
    """Derive parent progress + status from direct children only."""
    if not children:
        return 0, "todo"
    statuses = [c.status for c in children]
    progresses = [int(c.progress or 0) for c in children]
    if any(s == "blocked" for s in statuses):
        avg = sum(progresses) // len(children)
        return avg, "blocked"
    if all(s == "done" for s in statuses):
        return 100, "done"
    if all(s == "todo" for s in statuses):
        return 0, "todo"
    avg = sum(progresses) // len(children)
    if avg >= 100:
        return 100, "done"
    if avg <= 0:
        return 0, "todo"
    return avg, "in_progress"


def task_has_children(task_id: int) -> bool:
    """True when the task has at least one non-deleted direct child."""
    return (
        db.session.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.parent_id == task_id, Task.deleted_at.is_(None))
        ).scalar_one()
        > 0
    )


def parent_ids_with_children(task_ids: list[int]) -> set[int]:
    if not task_ids:
        return set()
    rows = db.session.execute(
        select(Task.parent_id)
        .where(Task.parent_id.in_(task_ids), Task.deleted_at.is_(None))
        .distinct()
    ).scalars().all()
    return set(rows)


def assert_status_change_allowed(task_id: int) -> None:
    if task_has_children(task_id):
        raise BadRequest(
            "HAS_CHILDREN",
            "存在子任务的任务不可单独修改状态，请通过子任务推进",
        )


def _sync_is_leaf_flag(task_id: int) -> None:
    """Display hint only: true when the node has no active children."""
    t = db.session.get(Task, task_id)
    if not t or t.deleted_at:
        return
    child_count = db.session.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.parent_id == task_id, Task.deleted_at.is_(None))
    ).scalar_one()
    t.is_leaf = child_count == 0


def _recompute_ancestors_progress(task_id: int) -> list[int]:
    """Walk from changed node up; recompute each parent's progress/status from children."""
    updated_ids: list[int] = []
    ancestor_ids = [
        r.ancestor_id
        for r in db.session.execute(
            select(TaskClosure).where(
                TaskClosure.descendant_id == task_id, TaskClosure.distance > 0
            ).order_by(TaskClosure.distance.asc())
        ).scalars().all()
    ]
    for aid in ancestor_ids:
        children = db.session.execute(
            select(Task).where(Task.parent_id == aid, Task.deleted_at.is_(None))
        ).scalars().all()
        if not children:
            continue
        parent = db.session.get(Task, aid)
        if not parent or parent.deleted_at:
            continue
        avg, stat = _aggregate_from_children(children)
        avg = _clamp_progress_for_status(avg, stat)
        if parent.progress == avg and parent.status == stat:
            continue
        parent.progress = avg
        parent.status = stat
        parent.version += 1
        updated_ids.append(aid)
    return updated_ids


# ---------- public API ----------


def _serialize_task(
    t: Task,
    assignees: list[int] | None = None,
    dependencies: list[int] | None = None,
    *,
    can_manage: bool | None = None,
) -> dict:
    return {
        "id": t.id,
        "parent_id": t.parent_id,
        "title": t.title,
        "description": t.description or "",
        "is_leaf": t.is_leaf,
        "can_manage": can_manage if can_manage is not None else False,
        "refined": t.refined,
        "start_date": t.start_date,
        "end_date": t.end_date,
        "status": t.status,
        "progress": t.progress,
        "depth": t.depth,
        "position": t.position,
        "path": t.path,
        "version": t.version,
        "assignees": assignees if assignees is not None else _assignees_of(t.id),
        "dependencies": dependencies if dependencies is not None else _deps_of(t.id),
    }


def _assignees_of(task_id: int) -> list[int]:
    return [
        r.user_id
        for r in db.session.execute(
            select(TaskAssignment).where(TaskAssignment.task_id == task_id)
        ).scalars().all()
    ]


def _deps_of(task_id: int) -> list[int]:
    return [
        r.depends_on
        for r in db.session.execute(
            select(TaskDependency).where(TaskDependency.task_id == task_id)
        ).scalars().all()
    ]


def get_tree(group_id: int, actor_id: int | None = None) -> dict:
    rows = db.session.execute(
        select(Task)
        .where(Task.group_id == group_id, Task.deleted_at.is_(None))
        .order_by(Task.path.asc(), Task.position.asc())
    ).scalars().all()
    if not rows:
        return {"group_id": group_id, "version": 0, "nodes": []}
    ids = [t.id for t in rows]
    assigns = db.session.execute(
        select(TaskAssignment).where(TaskAssignment.task_id.in_(ids))
    ).scalars().all()
    deps = db.session.execute(
        select(TaskDependency).where(TaskDependency.task_id.in_(ids))
    ).scalars().all()
    a_map: dict[int, list[int]] = {}
    for a in assigns:
        a_map.setdefault(a.task_id, []).append(a.user_id)
    d_map: dict[int, list[int]] = {}
    for d in deps:
        d_map.setdefault(d.task_id, []).append(d.depends_on)
    managed = managed_task_ids(actor_id, group_id) if actor_id is not None else None
    nodes = [
        _serialize_task(
            t,
            a_map.get(t.id, []),
            d_map.get(t.id, []),
            can_manage=managed is None or t.id in managed,
        )
        for t in rows
    ]
    version = max(t.version for t in rows)
    return {"group_id": group_id, "version": version, "nodes": nodes}


def create_node(group_id: int, actor_id: int, data: dict) -> dict:
    parent_id = data.get("parent_id")
    parent = None
    if parent_id:
        parent = db.session.get(Task, parent_id)
        if not parent or parent.group_id != group_id or parent.deleted_at:
            raise BadRequest("BAD_PARENT", "父节点不存在")
    assert_can_create_under_parent(actor_id, group_id, parent_id)
    assignees = data.get("assignees") or []
    _ensure_member(group_id, assignees)
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    if start_date and not end_date:
        from datetime import timedelta

        end_date = start_date + timedelta(days=7) if isinstance(start_date, date) else end_date
    if end_date and not start_date:
        start_date = end_date

    pos = data.get("position")
    if pos is None:
        pos = (db.session.execute(
            select(func.coalesce(func.max(Task.position), -1))
            .where(Task.parent_id == parent_id, Task.group_id == group_id)
        ).scalar_one() or -1) + 1

    with tx() as s:
        t = Task(
            group_id=group_id,
            parent_id=parent_id,
            title=data["title"],
            description=data.get("description", ""),
            is_leaf=True,
            start_date=start_date,
            end_date=end_date,
            position=pos,
            depth=(parent.depth + 1) if parent else 0,
            path="/",  # placeholder; updated post-flush
        )
        s.add(t)
        s.flush()
        t.path = _path_of(parent, t.id)
        _insert_closure_for_new(t.id, parent_id)
        _sync_is_leaf_flag(t.id)
        if parent:
            _sync_is_leaf_flag(parent.id)
        for uid in assignees:
            s.add(TaskAssignment(task_id=t.id, user_id=uid))
        sync_subtree_managers_from_assignees(actor_id, group_id, t.id, assignees)
        audit.record(actor_id, "tree.create_node", group_id=group_id,
                     target_type="task", target_id=t.id, payload={"title": t.title})
    return _serialize_task(t, can_manage=True)


def _can_assignee_update_status(actor_id: int, group_id: int, task_id: int, data: dict) -> bool:
    if can_manage_task(actor_id, group_id, task_id):
        return False
    allowed = {"status", "expected_version"}
    extra = set(data.keys()) - allowed
    if extra:
        return False
    return actor_id in _assignees_of(task_id)


def update_node(group_id: int, actor_id: int, task_id: int, data: dict) -> dict:
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id or t.deleted_at:
        raise NotFound("task")
    if not can_manage_task(actor_id, group_id, task_id) and not _can_assignee_update_status(
        actor_id, group_id, task_id, data
    ):
        raise Forbidden("无权编辑该任务")
    expected = data.get("expected_version")
    if expected is not None and expected != t.version:
        raise Conflict("VERSION_CONFLICT", "节点已被他人修改", detail={"current": t.version})
    new_assignees = data.pop("assignees", None)
    new_deps = data.pop("dependencies", None)
    data.pop("expected_version", None)
    if new_assignees is not None and not can_manage_task(actor_id, group_id, task_id):
        raise Forbidden("仅节点管理员可调整负责人")
    if new_deps is not None and not can_manage_task(actor_id, group_id, task_id):
        raise Forbidden("仅节点管理员可调整依赖")
    cascade_ids: list[int] = []
    nullable_date_fields = frozenset({"start_date", "end_date"})
    with tx() as s:
        for k, v in data.items():
            if not hasattr(t, k):
                continue
            # Allow explicit null to clear DDL; other None values are ignored.
            if v is None and k not in nullable_date_fields:
                continue
            setattr(t, k, v)
        t.version += 1
        if new_assignees is not None:
            _ensure_member(group_id, new_assignees)
            s.execute(db.delete(TaskAssignment).where(TaskAssignment.task_id == task_id))
            for uid in new_assignees:
                s.add(TaskAssignment(task_id=task_id, user_id=uid))
            sync_subtree_managers_from_assignees(
                actor_id, group_id, task_id, new_assignees
            )
        if new_deps is not None:
            s.execute(db.delete(TaskDependency).where(TaskDependency.task_id == task_id))
            for d in new_deps:
                if d == task_id:
                    continue
                s.add(TaskDependency(task_id=task_id, depends_on=d))
        audit.record(actor_id, "tree.update_node", group_id=group_id,
                     target_type="task", target_id=task_id, payload=data)
        if "status" in data:
            new_status = data["status"]
            if new_status not in TASK_STATUS:
                raise BadRequest("BAD_STATUS", "无效的状态")
            if new_status != t.status:
                assert_status_change_allowed(task_id)
            t.progress = _progress_for_status(new_status, t.progress or 0)
            cascade_ids = _recompute_ancestors_progress(task_id)
            push_ws(group_id, "tree.updated", {"group_id": group_id})
    result = _serialize_task(t, can_manage=can_manage_task(actor_id, group_id, task_id))
    if cascade_ids:
        managed = managed_task_ids(actor_id, group_id)
        result["cascade"] = [
            _serialize_task(
                p,
                can_manage=managed is None or p.id in managed,
            )
            for aid in cascade_ids
            if (p := db.session.get(Task, aid)) and not p.deleted_at
        ]
    return result


def delete_node(group_id: int, actor_id: int, task_id: int):
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id:
        raise NotFound("task")
    assert_can_manage_task(actor_id, group_id, task_id)
    from ...common.datetime_util import utc_now

    parent_id = t.parent_id
    with tx() as s:
        desc_ids = _all_descendants(task_id)
        s.execute(db.update(Task).where(Task.id.in_(desc_ids)).values(deleted_at=utc_now()))
        if parent_id:
            _sync_is_leaf_flag(parent_id)
            _recompute_ancestors_progress(task_id)
        audit.record(actor_id, "tree.delete_node", group_id=group_id,
                     target_type="task", target_id=task_id,
                     payload={"descendants": desc_ids})


def move_node(group_id: int, actor_id: int, task_id: int, new_parent_id: int | None,
              new_position: int | None):
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id:
        raise NotFound("task")
    assert_can_manage_task(actor_id, group_id, task_id)
    if new_parent_id is not None:
        assert_can_create_under_parent(actor_id, group_id, new_parent_id)
    old_parent_id = t.parent_id
    if new_parent_id == task_id or new_parent_id in _all_descendants(task_id):
        raise BadRequest("CYCLE", "不能移动到自己的子孙下")
    new_parent = db.session.get(Task, new_parent_id) if new_parent_id else None
    if new_parent and (new_parent.group_id != group_id or new_parent.deleted_at):
        raise BadRequest("BAD_PARENT", "目标父节点无效")
    with tx():
        _detach_subtree_closure(task_id)
        t.parent_id = new_parent_id
        if new_position is not None:
            t.position = new_position
        else:
            t.position = (db.session.execute(
                select(func.coalesce(func.max(Task.position), -1))
                .where(Task.parent_id == new_parent_id, Task.group_id == group_id)
            ).scalar_one() or -1) + 1
        _attach_subtree_closure(task_id, new_parent_id)
        _rebuild_paths(task_id)
        _sync_is_leaf_flag(task_id)
        if old_parent_id:
            _sync_is_leaf_flag(old_parent_id)
        if new_parent_id:
            _sync_is_leaf_flag(new_parent_id)
        _recompute_ancestors_progress(task_id)
        audit.record(actor_id, "tree.move_node", group_id=group_id,
                     target_type="task", target_id=task_id,
                     payload={"new_parent_id": new_parent_id})


def task_path_keywords(group_id: int, task_id: int) -> list[str]:
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id or t.deleted_at:
        raise NotFound("task")
    titles: list[str] = []
    if t.path:
        for seg in t.path.strip("/").split("/"):
            if not seg.isdigit():
                continue
            node = db.session.get(Task, int(seg))
            if node and node.title:
                title = node.title.strip()
                if title and (not titles or titles[-1] != title):
                    titles.append(title)
    elif t.title:
        titles.append(t.title.strip())
    return titles


def get_related_inspiration(group_id: int, task_id: int, viewer_id: int) -> dict:
    from ..inspiration.service import related_posts_union

    keywords = task_path_keywords(group_id, task_id)
    return related_posts_union(viewer_id, keywords, limit=12)


def get_node_managers(group_id: int, task_id: int) -> list[dict]:
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id or t.deleted_at:
        raise NotFound("task")
    return list_node_managers(group_id, task_id)


def add_node_manager(group_id: int, actor_id: int, task_id: int, user_id: int) -> dict:
    """Legacy API: adds assignee (assignee = subtree manager)."""
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id or t.deleted_at:
        raise NotFound("task")
    assert_can_manage_task(actor_id, group_id, task_id)
    ids = list(_assignees_of(task_id))
    if user_id not in ids:
        ids.append(user_id)
    with tx() as s:
        _ensure_member(group_id, ids)
        s.execute(db.delete(TaskAssignment).where(TaskAssignment.task_id == task_id))
        for uid in ids:
            s.add(TaskAssignment(task_id=task_id, user_id=uid))
        sync_subtree_managers_from_assignees(actor_id, group_id, task_id, ids)
        t.version += 1
    row = list_node_managers(group_id, task_id)
    for m in row:
        if m["user_id"] == user_id:
            return m
    return grant_node_manager(actor_id, group_id, task_id, user_id)


def remove_node_manager(group_id: int, actor_id: int, task_id: int, user_id: int) -> None:
    """Legacy API: removes assignee."""
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id or t.deleted_at:
        raise NotFound("task")
    assert_can_manage_task(actor_id, group_id, task_id)
    ids = [u for u in _assignees_of(task_id) if u != user_id]
    with tx() as s:
        s.execute(db.delete(TaskAssignment).where(TaskAssignment.task_id == task_id))
        for uid in ids:
            s.add(TaskAssignment(task_id=task_id, user_id=uid))
        sync_subtree_managers_from_assignees(actor_id, group_id, task_id, ids)
        t.version += 1


def replace_tree(group_id: int, actor_id: int, payload: dict) -> dict:
    """Whole-tree replacement (used by 'AI generated → confirm' and templates)."""
    expected = payload.get("expected_version")
    cur = db.session.execute(
        select(func.max(Task.version)).where(
            Task.group_id == group_id, Task.deleted_at.is_(None)
        )
    ).scalar_one()
    if expected is not None and cur and expected != cur:
        raise Conflict("VERSION_CONFLICT", "项目树版本不一致", detail={"current": cur})

    from ...common.datetime_util import utc_now

    with tx() as s:
        # Soft-delete existing
        s.execute(
            db.update(Task).where(
                Task.group_id == group_id, Task.deleted_at.is_(None)
            ).values(deleted_at=utc_now())
        )

        new_ids: list[int] = []

        def _create_recursive(node_data: dict, parent_id: int | None, position: int):
            t = Task(
                group_id=group_id,
                parent_id=parent_id,
                title=node_data["title"][:256],
                description=node_data.get("description", ""),
                is_leaf=not (node_data.get("children") or []),
                start_date=node_data.get("start_date"),
                end_date=node_data.get("end_date"),
                position=position,
                depth=0,
                path="/",
            )
            s.add(t)
            s.flush()
            t.path = (
                f"{db.session.get(Task, parent_id).path}{t.id}/"
                if parent_id else f"/{t.id}/"
            )
            t.depth = (db.session.get(Task, parent_id).depth + 1) if parent_id else 0
            _insert_closure_for_new(t.id, parent_id)
            for uid in node_data.get("assignees", []) or []:
                s.add(TaskAssignment(task_id=t.id, user_id=uid))
            new_ids.append(t.id)
            for i, child in enumerate(node_data.get("children", []) or []):
                _create_recursive(child, t.id, i)

        for i, root in enumerate(payload["nodes"]):
            _create_recursive(root, None, i)

        audit.record(actor_id, "tree.replace", group_id=group_id,
                     payload={"new_root_count": len(payload["nodes"])})

    return get_tree(group_id)
