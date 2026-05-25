from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select

from ...extensions import db, get_redis
from ...models import Group, GroupMember, Task, TaskAssignment


def get_dashboard(uid: int) -> dict:
    today = date.today()
    rows = db.session.execute(
        select(Task, Group)
        .join(Group, Group.id == Task.group_id)
        .join(TaskAssignment, TaskAssignment.task_id == Task.id)
        .where(
            TaskAssignment.user_id == uid,
            Task.is_leaf.is_(True),
            Task.deleted_at.is_(None),
            Task.status.in_(["todo", "in_progress", "blocked"]),
            Group.status == "active",
        )
        .order_by(Task.end_date.asc())
        .limit(100)
    ).all()

    tasks = []
    urgent = []
    for t, g in rows:
        days_left = (t.end_date - today).days if t.end_date else 999
        is_urgent = days_left <= 1 and t.status != "done"
        item = {
            "task_id": t.id,
            "title": t.title,
            "group_id": g.id,
            "group_name": g.name,
            "course_name": g.course_name,
            "end_date": t.end_date,
            "status": t.status,
            "progress": t.progress,
            "urgent": is_urgent,
            "days_left": days_left,
        }
        tasks.append(item)
        if is_urgent:
            urgent.append(item)

    # Leader summary
    leader_rows = db.session.execute(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == uid, GroupMember.role == "leader",
               Group.status == "active")
    ).scalars().all()
    leader_groups = []
    for g in leader_rows:
        stats = db.session.execute(
            select(Task.status, func.count(), func.avg(Task.progress))
            .where(Task.group_id == g.id, Task.is_leaf.is_(True), Task.deleted_at.is_(None))
            .group_by(Task.status)
        ).all()
        counts = {"todo": 0, "in_progress": 0, "done": 0, "blocked": 0}
        progs = []
        for status, cnt, prog in stats:
            counts[status] = int(cnt)
            if prog is not None:
                progs.append(float(prog))
        urgent_cnt = db.session.execute(
            select(func.count()).select_from(Task).where(
                Task.group_id == g.id, Task.is_leaf.is_(True),
                Task.deleted_at.is_(None),
                Task.status != "done",
                Task.end_date <= today,
            )
        ).scalar_one()
        leader_groups.append({
            "group_id": g.id,
            "course_name": g.course_name,
            "name": g.name,
            "progress": int(sum(progs) / len(progs)) if progs else 0,
            **counts,
            "urgent_count": int(urgent_cnt),
        })

    return {"tasks": tasks, "urgent": urgent, "leader_groups": leader_groups}


def get_daily_advice(uid: int) -> dict:
    """Get cached daily advice; if missing, kick off AI generation synchronously (cheap fallback)."""
    r = get_redis()
    today_str = date.today().isoformat()
    cache_key = f"advice:{uid}:{today_str}"
    cached = r.get(cache_key)
    if cached:
        import json
        data = json.loads(cached)
        ga = data.get("generated_at")
        if isinstance(ga, str):
            data["generated_at"] = datetime.fromisoformat(ga)
        return data | {"cached": True}

    # Build context
    dash = get_dashboard(uid)
    if not dash["tasks"]:
        result = {
            "advice": "今天暂时没有进行中的任务，可以浏览灵感广场或更新个人技能标签。",
            "suggestions": ["浏览灵感广场最热模板", "完善技能标签便于AI智能分工"],
            "generated_at": datetime.utcnow(),
            "cached": False,
        }
    else:
        # Cheap heuristic-based advice; AI version overrides if available
        urgent = dash["urgent"]
        top = dash["tasks"][0]
        sugs = []
        if urgent:
            sugs.append(f"先攻克紧急任务「{urgent[0]['title']}」，距离 DDL 仅 {urgent[0]['days_left']} 天")
        sugs.append(f"今日重点推进：「{top['title']}」")
        if len(dash["tasks"]) > 3:
            sugs.append(f"还有 {len(dash['tasks']) - 1} 项待办，建议按 DDL 顺序处理")
        result = {
            "advice": f"你今天有 {len(dash['tasks'])} 项待办，其中 {len(urgent)} 项紧急。",
            "suggestions": sugs,
            "generated_at": datetime.utcnow(),
            "cached": False,
        }

    import json
    r.setex(cache_key, 86400, json.dumps({
        "advice": result["advice"],
        "suggestions": result["suggestions"],
        "generated_at": result["generated_at"].isoformat(),
    }))
    return result
