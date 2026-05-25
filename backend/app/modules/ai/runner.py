"""High-level AI 'scope' runners. Each runner: builds prompt → calls LLM → validates with schema."""
from __future__ import annotations

import json
import logging
import pathlib
from datetime import date, timedelta

from sqlalchemy import select

from ...extensions import db
from ...models import AiConversation, AiMessage, GroupMember, Task, User, UserSkill
from .client import call_llm, parse_json
from .schemas import (
    AssignmentOut,
    DailyAdviceOut,
    TreeEditOut,
    TreeGenOut,
    validate_tree,
)

log = logging.getLogger(__name__)
PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _record(conv_id: int, role: str, content: str, tokens_in: int = 0, tokens_out: int = 0):
    db.session.add(AiMessage(
        conversation_id=conv_id, role=role, content=content,
        tokens_in=tokens_in, tokens_out=tokens_out,
    ))


def _group_members_for_ai(group_id: int) -> list[dict]:
    rows = db.session.execute(
        select(GroupMember, User).join(User, User.id == GroupMember.user_id)
        .where(GroupMember.group_id == group_id)
    ).all()
    out = []
    for m, u in rows:
        skills = [
            s.skill for s in db.session.execute(
                select(UserSkill).where(UserSkill.user_id == u.id)
            ).scalars().all()
        ]
        out.append({"user_id": u.id, "name": u.name, "role": m.role, "skills": skills})
    return out


def run_tree_gen(conv: AiConversation, document: str) -> dict:
    system = _load_prompt("tree_gen")
    members = _group_members_for_ai(conv.group_id) if conv.group_id else []
    today = date.today()
    user_msg = json.dumps({
        "document": document[:8000],
        "members": members,
        "context": {"today": today.isoformat(), "course_end": (today + timedelta(weeks=12)).isoformat()},
    }, ensure_ascii=False)

    text, ti, to, provider = call_llm(
        system=system.replace("{document}", "(see user)").replace("{members}", "(see user)").replace("{context}", "(see user)"),
        user=user_msg,
        json_mode=True,
        max_tokens=6000,
    )
    _record(conv.id, "user", user_msg)
    _record(conv.id, "assistant", text, ti, to)

    parsed = parse_json(text)
    out = TreeGenOut(**parsed)
    validate_tree(out)
    return out.model_dump(mode="json")


def run_tree_edit(conv: AiConversation, current_tree: dict, instruction: str) -> dict:
    system = _load_prompt("tree_edit")
    user_msg = json.dumps({
        "current_tree": current_tree,
        "instruction": instruction,
    }, ensure_ascii=False)
    text, ti, to, _ = call_llm(system=system, user=user_msg, json_mode=True, max_tokens=6000)
    _record(conv.id, "user", user_msg)
    _record(conv.id, "assistant", text, ti, to)
    parsed = parse_json(text)
    out = TreeEditOut(**parsed)
    validate_tree(out)
    return out.model_dump(mode="json")


def run_daily_advice(conv: AiConversation, context: dict) -> dict:
    system = _load_prompt("daily_advice")
    user_msg = json.dumps(context, ensure_ascii=False, default=str)
    text, ti, to, _ = call_llm(system=system, user=user_msg, json_mode=True, max_tokens=800)
    _record(conv.id, "user", user_msg)
    _record(conv.id, "assistant", text, ti, to)
    parsed = parse_json(text)
    return DailyAdviceOut(**parsed).model_dump()


def run_assignment(conv: AiConversation, tasks: list[dict]) -> dict:
    members = _group_members_for_ai(conv.group_id)
    # estimate load
    from sqlalchemy import func
    from ...models import TaskAssignment
    loads = {}
    for m in members:
        cnt = db.session.execute(
            select(func.count()).select_from(TaskAssignment).join(
                Task, Task.id == TaskAssignment.task_id
            ).where(
                TaskAssignment.user_id == m["user_id"],
                Task.group_id == conv.group_id,
                Task.is_leaf.is_(True),
                Task.deleted_at.is_(None),
                Task.status != "done",
            )
        ).scalar_one()
        loads[m["user_id"]] = int(cnt)
    for m in members:
        m["current_load"] = loads.get(m["user_id"], 0)

    system = _load_prompt("assignment")
    user_msg = json.dumps({"tasks": tasks, "members": members}, ensure_ascii=False)
    text, ti, to, _ = call_llm(system=system, user=user_msg, json_mode=True, max_tokens=1500)
    _record(conv.id, "user", user_msg)
    _record(conv.id, "assistant", text, ti, to)
    parsed = parse_json(text)
    return AssignmentOut(**parsed).model_dump()
