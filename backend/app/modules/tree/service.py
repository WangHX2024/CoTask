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
from ...common.errors import BadRequest, Conflict, NotFound
from ...common.tx import tx
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


def _recompute_ancestors_progress(task_id: int):
    """Walk from `task_id` up the tree; for each non-leaf, recompute progress from children."""
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
        total = sum(c.progress for c in children)
        avg = total // len(children)
        parent = db.session.get(Task, aid)
        parent.progress = avg
        if avg == 100:
            parent.status = "done"
        elif avg == 0:
            parent.status = "todo"
        else:
            parent.status = "in_progress"


# ---------- public API ----------


def _serialize_task(t: Task, assignees: list[int] | None = None,
                   dependencies: list[int] | None = None) -> dict:
    return {
        "id": t.id,
        "parent_id": t.parent_id,
        "title": t.title,
        "description": t.description or "",
        "is_leaf": t.is_leaf,
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


def get_tree(group_id: int) -> dict:
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
    nodes = [_serialize_task(t, a_map.get(t.id, []), d_map.get(t.id, [])) for t in rows]
    version = max(t.version for t in rows)
    return {"group_id": group_id, "version": version, "nodes": nodes}


def create_node(group_id: int, actor_id: int, data: dict) -> dict:
    parent_id = data.get("parent_id")
    parent = None
    if parent_id:
        parent = db.session.get(Task, parent_id)
        if not parent or parent.group_id != group_id or parent.deleted_at:
            raise BadRequest("BAD_PARENT", "父节点不存在")
    assignees = data.get("assignees") or []
    _ensure_member(group_id, assignees)
    is_leaf = bool(data.get("is_leaf"))
    if is_leaf and (not data.get("start_date") or not data.get("end_date")):
        # default to 7 days from today
        from datetime import timedelta
        today = date.today()
        data["start_date"] = data.get("start_date") or today
        data["end_date"] = data.get("end_date") or today + timedelta(days=7)

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
            is_leaf=is_leaf,
            start_date=data.get("start_date") if is_leaf else None,
            end_date=data.get("end_date") if is_leaf else None,
            position=pos,
            depth=(parent.depth + 1) if parent else 0,
            path="/",  # placeholder; updated post-flush
        )
        s.add(t)
        s.flush()
        t.path = _path_of(parent, t.id)
        _insert_closure_for_new(t.id, parent_id)
        if parent:
            # parent is no longer a leaf
            if parent.is_leaf:
                parent.is_leaf = False
                parent.start_date = None
                parent.end_date = None
        for uid in assignees:
            s.add(TaskAssignment(task_id=t.id, user_id=uid))
        audit.record(actor_id, "tree.create_node", group_id=group_id,
                     target_type="task", target_id=t.id, payload={"title": t.title})
    return _serialize_task(t)


def update_node(group_id: int, actor_id: int, task_id: int, data: dict) -> dict:
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id or t.deleted_at:
        raise NotFound("task")
    expected = data.get("expected_version")
    if expected is not None and expected != t.version:
        raise Conflict("VERSION_CONFLICT", "节点已被他人修改", detail={"current": t.version})
    new_assignees = data.pop("assignees", None)
    new_deps = data.pop("dependencies", None)
    data.pop("expected_version", None)
    with tx() as s:
        for k, v in data.items():
            if v is not None and hasattr(t, k):
                setattr(t, k, v)
        t.version += 1
        if new_assignees is not None:
            _ensure_member(group_id, new_assignees)
            s.execute(db.delete(TaskAssignment).where(TaskAssignment.task_id == task_id))
            for uid in new_assignees:
                s.add(TaskAssignment(task_id=task_id, user_id=uid))
        if new_deps is not None:
            s.execute(db.delete(TaskDependency).where(TaskDependency.task_id == task_id))
            for d in new_deps:
                if d == task_id:
                    continue
                s.add(TaskDependency(task_id=task_id, depends_on=d))
        audit.record(actor_id, "tree.update_node", group_id=group_id,
                     target_type="task", target_id=task_id, payload=data)
        if "status" in data and t.is_leaf:
            t.progress = 100 if data["status"] == "done" else (0 if data["status"] == "todo" else t.progress or 50)
            _recompute_ancestors_progress(task_id)
    return _serialize_task(t)


def delete_node(group_id: int, actor_id: int, task_id: int):
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id:
        raise NotFound("task")
    from datetime import datetime
    with tx() as s:
        desc_ids = _all_descendants(task_id)
        s.execute(db.update(Task).where(Task.id.in_(desc_ids)).values(deleted_at=datetime.utcnow()))
        if t.parent_id:
            _recompute_ancestors_progress(task_id)
        audit.record(actor_id, "tree.delete_node", group_id=group_id,
                     target_type="task", target_id=task_id,
                     payload={"descendants": desc_ids})


def move_node(group_id: int, actor_id: int, task_id: int, new_parent_id: int | None,
              new_position: int | None):
    t = db.session.get(Task, task_id)
    if not t or t.group_id != group_id:
        raise NotFound("task")
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
        _recompute_ancestors_progress(task_id)
        audit.record(actor_id, "tree.move_node", group_id=group_id,
                     target_type="task", target_id=task_id,
                     payload={"new_parent_id": new_parent_id})


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

    from datetime import datetime

    with tx() as s:
        # Soft-delete existing
        s.execute(
            db.update(Task).where(
                Task.group_id == group_id, Task.deleted_at.is_(None)
            ).values(deleted_at=datetime.utcnow())
        )

        new_ids: list[int] = []

        def _create_recursive(node_data: dict, parent_id: int | None, position: int):
            t = Task(
                group_id=group_id,
                parent_id=parent_id,
                title=node_data["title"][:256],
                description=node_data.get("description", ""),
                is_leaf=bool(node_data.get("is_leaf", False)) or not node_data.get("children"),
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
