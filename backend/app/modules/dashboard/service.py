from __future__ import annotations

import json
from datetime import date, timedelta

from sqlalchemy import and_, exists, func, or_, select

from ...common.datetime_util import app_today, to_api_datetime, utc_now
from ...extensions import db, get_redis
from ...models import Group, GroupMember, Task, TaskAssignment, User
from ..groups.service import group_average_progress
from ..tree.service import parent_ids_with_children

_OPEN_STATUSES = ("todo", "in_progress", "blocked")
_DONE_RECENT_DAYS = 60


def _urgency_level(end_date: date | None, today: date, status: str) -> str | None:
    """critical ≈ 24h window (overdue / today / tomorrow); warning ≈ within 72h."""
    if status == "done" or not end_date:
        return None
    days_left = (end_date - today).days
    if days_left < 0 or days_left <= 1:
        return "critical"
    if days_left <= 3:
        return "warning"
    return None


def _assignees_map(task_ids: list[int]) -> dict[int, list[dict]]:
    if not task_ids:
        return {}
    rows = db.session.execute(
        select(TaskAssignment.task_id, User.id, User.name, User.avatar_url)
        .join(User, User.id == TaskAssignment.user_id)
        .where(TaskAssignment.task_id.in_(task_ids))
    ).all()
    out: dict[int, list[dict]] = {}
    for tid, uid, name, avatar_url in rows:
        out.setdefault(tid, []).append(
            {"user_id": uid, "name": name or "", "avatar_url": avatar_url or None}
        )
    return out


def _ancestor_ids_from_tasks(tasks: list[Task]) -> set[int]:
    ids: set[int] = set()
    for t in tasks:
        for seg in (t.path or "").strip("/").split("/"):
            if seg.isdigit():
                ids.add(int(seg))
    return ids


def _title_by_id(task_ids: set[int]) -> dict[int, str]:
    if not task_ids:
        return {}
    rows = db.session.execute(
        select(Task.id, Task.title).where(Task.id.in_(task_ids))
    ).all()
    return {tid: title for tid, title in rows}


def _title_path(t: Task, titles: dict[int, str]) -> str:
    parts: list[str] = []
    for seg in (t.path or "").strip("/").split("/"):
        if not seg.isdigit():
            continue
        name = titles.get(int(seg))
        if name:
            parts.append(name)
    return " / ".join(parts) if parts else t.title


def _serialize_task(
    t: Task,
    g: Group,
    today: date,
    assignees: list[dict],
    *,
    titles: dict[int, str],
    has_children: bool = False,
) -> dict:
    days_left = (t.end_date - today).days if t.end_date else None
    level = _urgency_level(t.end_date, today, t.status)
    return {
        "task_id": t.id,
        "title": t.title,
        "title_path": _title_path(t, titles),
        "group_id": g.id,
        "group_name": g.name,
        "course_name": g.course_name,
        "start_date": t.start_date,
        "end_date": t.end_date,
        "status": t.status,
        "progress": t.progress or 0,
        "has_children": has_children,
        "urgent": level == "critical",
        "urgency_level": level,
        "days_left": days_left if days_left is not None else 999,
        "assignees": assignees,
    }


def _leader_urgent_counts(group_id: int, today: date) -> tuple[int, int]:
    """critical count, due_soon (critical+warning) count for open tasks with DDL."""
    rows = db.session.execute(
        select(Task.end_date, Task.status).where(
            Task.group_id == group_id,
            Task.deleted_at.is_(None),
            Task.end_date.is_not(None),
            Task.status.in_(["todo", "in_progress", "blocked"]),
        )
    ).all()
    critical = warning = 0
    for end_date, status in rows:
        level = _urgency_level(end_date, today, status)
        if level == "critical":
            critical += 1
        if level in ("critical", "warning"):
            warning += 1
    return critical, warning


def _sort_scheduled_rows(rows: list[tuple[Task, Group]], today: date) -> list[tuple[Task, Group]]:
    """Open tasks by ascending DDL; completed tasks after, most recent end_date first."""

    def sort_key(pair: tuple[Task, Group]) -> tuple[int, int]:
        t, _ = pair
        if t.status == "done":
            ed = t.end_date or today
            return (1, -ed.toordinal())
        days = (t.end_date - today).days if t.end_date else 9999
        return (0, days)

    return sorted(rows, key=sort_key)


def get_dashboard(uid: int) -> dict:
    today = app_today()
    assignment_base = (
        TaskAssignment.user_id == uid,
        Task.deleted_at.is_(None),
        Group.status == "active",
    )
    open_status = Task.status.in_(_OPEN_STATUSES)
    done_recent_cutoff = today - timedelta(days=_DONE_RECENT_DAYS)

    scheduled_rows = db.session.execute(
        select(Task, Group)
        .join(Group, Group.id == Task.group_id)
        .join(TaskAssignment, TaskAssignment.task_id == Task.id)
        .where(
            *assignment_base,
            Task.end_date.is_not(None),
            or_(
                open_status,
                and_(Task.status == "done", Task.end_date >= done_recent_cutoff),
            ),
        )
        .limit(200)
    ).all()
    scheduled_rows = _sort_scheduled_rows(list(scheduled_rows), today)[:150]

    unscheduled_rows = db.session.execute(
        select(Task, Group)
        .join(Group, Group.id == Task.group_id)
        .join(TaskAssignment, TaskAssignment.task_id == Task.id)
        .where(*assignment_base, open_status, Task.end_date.is_(None))
        .order_by(Task.updated_at.desc())
        .limit(50)
    ).all()

    all_task_objs = [t for t, _ in scheduled_rows] + [t for t, _ in unscheduled_rows]
    all_ids = [t.id for t in all_task_objs]
    amap = _assignees_map(all_ids)
    titles = _title_by_id(_ancestor_ids_from_tasks(all_task_objs))
    parents_with_children = parent_ids_with_children(all_ids)

    tasks = []
    urgent_critical = []
    urgent_warning = []
    for t, g in scheduled_rows:
        item = _serialize_task(
            t,
            g,
            today,
            amap.get(t.id, []),
            titles=titles,
            has_children=t.id in parents_with_children,
        )
        tasks.append(item)
        if item["urgency_level"] == "critical":
            urgent_critical.append(item)
        elif item["urgency_level"] == "warning":
            urgent_warning.append(item)

    unscheduled = [
        _serialize_task(
            t,
            g,
            today,
            amap.get(t.id, []),
            titles=titles,
            has_children=t.id in parents_with_children,
        )
        for t, g in unscheduled_rows
    ]

    leader_rows = db.session.execute(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(
            GroupMember.user_id == uid,
            GroupMember.role == "leader",
            Group.status == "active",
        )
    ).scalars().all()

    leader_groups = []
    for g in leader_rows:
        stats = db.session.execute(
            select(Task.status, func.count())
            .where(Task.group_id == g.id, Task.deleted_at.is_(None))
            .group_by(Task.status)
        ).all()
        counts = {"todo": 0, "in_progress": 0, "done": 0, "blocked": 0}
        for status, cnt in stats:
            counts[status] = int(cnt)
        critical_cnt, due_soon_cnt = _leader_urgent_counts(g.id, today)
        unassigned = int(
            db.session.execute(
                select(func.count()).select_from(Task).where(
                    Task.group_id == g.id,
                    Task.deleted_at.is_(None),
                    Task.status.in_(["todo", "in_progress", "blocked"]),
                    ~exists(select(1).where(TaskAssignment.task_id == Task.id)),
                )
            ).scalar_one()
        )
        leader_groups.append({
            "group_id": g.id,
            "course_name": g.course_name,
            "name": g.name,
            "progress": group_average_progress(g.id),
            **counts,
            "urgent_count": critical_cnt,
            "due_soon_count": due_soon_cnt,
            "unassigned_count": unassigned,
        })

    open_count = sum(1 for t in tasks if t["status"] != "done") + len(unscheduled)
    return {
        "tasks": tasks,
        "unscheduled": unscheduled,
        "urgent": urgent_critical,
        "urgent_warning": urgent_warning,
        "leader_groups": leader_groups,
        "focus": {
            "open_count": open_count,
            "critical_count": len(urgent_critical),
            "warning_count": len(urgent_warning),
        },
    }


def build_advice_context(dash: dict) -> dict:
    return {
        "tasks": dash.get("tasks", [])[:30],
        "urgent": dash.get("urgent", [])[:10],
        "leader_groups": dash.get("leader_groups", []),
    }


def cache_daily_advice(uid: int, result: dict) -> None:
    r = get_redis()
    today_str = app_today().isoformat()
    payload = {
        "advice": result.get("advice", ""),
        "suggestions": result.get("suggestions", []),
        "generated_at": to_api_datetime(utc_now()),
    }
    r.setex(f"advice:{uid}:{today_str}", 86400, json.dumps(payload, ensure_ascii=False))


def _heuristic_advice(dash: dict) -> dict:
    if not dash["tasks"] and not dash.get("unscheduled"):
        return {
            "advice": "今天暂时没有进行中的任务，可以浏览灵感广场或更新个人技能标签。",
            "suggestions": ["浏览灵感广场最热模板", "完善技能标签便于 AI 智能分工"],
            "generated_at": utc_now(),
            "cached": False,
        }
    urgent = dash["urgent"]
    top = dash["tasks"][0] if dash["tasks"] else dash["unscheduled"][0]
    sugs = []
    if urgent:
        u0 = urgent[0]
        sugs.append(
            f"先攻克紧急任务「{u0['title']}」"
            + (f"，距离 DDL 仅 {u0['days_left']} 天" if u0.get("days_left", 99) <= 3 else "")
        )
    sugs.append(f"今日重点推进：「{top['title']}」")
    open_n = dash["focus"]["open_count"]
    if open_n > 3:
        sugs.append(f"还有 {open_n - 1} 项待办，建议按 DDL 顺序处理")
    return {
        "advice": f"你今天有 {open_n} 项待办，其中 {dash['focus']['critical_count']} 项紧急。",
        "suggestions": sugs[:5],
        "generated_at": utc_now(),
        "cached": False,
    }


def get_daily_advice(uid: int, dash: dict | None = None) -> dict:
    """Return cached or heuristic advice (no LLM on plain GET)."""
    r = get_redis()
    today_str = app_today().isoformat()
    cache_key = f"advice:{uid}:{today_str}"
    cached = r.get(cache_key)
    if cached:
        import json as _json

        data = _json.loads(cached)
        ga = data.get("generated_at")
        if isinstance(ga, str):
            from datetime import datetime

            data["generated_at"] = datetime.fromisoformat(ga.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        return data | {"cached": True}

    dash = dash or get_dashboard(uid)
    result = _heuristic_advice(dash)
    cache_daily_advice(uid, result)
    return result | {"cached": False}


def get_overview(uid: int, *, include_advice: bool = True) -> dict:
    """Single round-trip payload for dashboard page."""
    dash = get_dashboard(uid)
    if include_advice:
        dash["advice"] = get_daily_advice(uid, dash=dash)
    return dash


def refresh_daily_advice_job(uid: int) -> int:
    """Enqueue Celery AI job; returns conversation id."""
    dash = get_dashboard(uid)
    from ..ai.service import create_job

    conv = create_job(uid, "daily_advice", None, build_advice_context(dash))
    return conv.id
