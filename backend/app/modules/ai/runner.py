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


def _working_tree(conv: AiConversation) -> dict:
    res = conv.result or {}
    nodes = res.get("nodes") if isinstance(res, dict) else None
    if isinstance(nodes, list) and nodes:
        return {"nodes": nodes}
    ctx = conv.context or {}
    return ctx.get("current_tree") or {"nodes": []}


def _user_message_text(content: str) -> str:
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return (data.get("instruction") or data.get("document") or "").strip()
    except json.JSONDecodeError:
        pass
    return (content or "").strip()


def _assistant_summary(content: str) -> str:
    try:
        data = parse_json(content)
        return (data.get("diff_summary") or data.get("summary") or "").strip()
    except Exception:
        return (content or "")[:200]


def _load_prior_turns(conv_id: int) -> list[dict]:
    rows = db.session.execute(
        select(AiMessage)
        .where(AiMessage.conversation_id == conv_id, AiMessage.role.in_(["user", "assistant"]))
        .order_by(AiMessage.id)
    ).scalars().all()
    turns: list[dict] = []
    for m in rows:
        if m.role == "user":
            text = _user_message_text(m.content)
            if text:
                turns.append({"role": "user", "text": text})
        else:
            summary = _assistant_summary(m.content)
            if summary:
                turns.append({"role": "assistant", "text": summary})
    return turns


def run_tree_gen(conv: AiConversation) -> dict:
    system = _load_prompt("tree_gen")
    ctx = conv.context or {}
    document = (ctx.get("document") or "").strip()
    instruction = (ctx.get("instruction") or "").strip()
    members = _group_members_for_ai(conv.group_id) if conv.group_id else []
    today = date.today()
    date_ctx = {
        "today": today.isoformat(),
        "course_end": (today + timedelta(weeks=12)).isoformat(),
    }
    working = _working_tree(conv)
    history = _load_prior_turns(conv.id)
    refine = bool(working.get("nodes")) or len(history) > 0

    if refine:
        user_text = instruction or document
        _record(conv.id, "user", user_text)
        user_msg = json.dumps({
            "mode": "refine",
            "document": document[:8000],
            "draft_tree": working,
            "history": history,
            "instruction": user_text,
            "members": members,
            "context": date_ctx,
        }, ensure_ascii=False)
    else:
        if not document:
            raise ValueError("document required for tree generation")
        _record(conv.id, "user", document[:8000])
        user_msg = json.dumps({
            "mode": "generate",
            "document": document[:8000],
            "members": members,
            "context": date_ctx,
        }, ensure_ascii=False)

    text, ti, to, _provider = call_llm(
        system=system.replace("{document}", "(see user)").replace("{members}", "(see user)").replace("{context}", "(see user)"),
        user=user_msg,
        json_mode=True,
        max_tokens=6000,
    )
    _record(conv.id, "assistant", text, ti, to)

    parsed = parse_json(text)
    out = TreeGenOut(**parsed)
    member_ids = {m["user_id"] for m in members}
    validate_tree(out, member_ids=member_ids if member_ids else None)
    return out.model_dump(mode="json")


def run_tree_edit(conv: AiConversation) -> dict:
    system = _load_prompt("tree_edit")
    ctx = conv.context or {}
    instruction = (ctx.get("instruction") or "").strip()
    if not instruction:
        raise ValueError("instruction required")
    original = ctx.get("current_tree") or {"nodes": []}
    working = _working_tree(conv)
    history = _load_prior_turns(conv.id)
    members = _group_members_for_ai(conv.group_id) if conv.group_id else []
    member_ids = {m["user_id"] for m in members}

    _record(conv.id, "user", instruction)
    user_msg = json.dumps({
        "original_tree": original,
        "working_tree": working,
        "history": history,
        "instruction": instruction,
        "members": members,
    }, ensure_ascii=False)
    text, ti, to, _ = call_llm(system=system, user=user_msg, json_mode=True, max_tokens=6000)
    _record(conv.id, "assistant", text, ti, to)
    parsed = parse_json(text)
    out = TreeEditOut(**parsed)
    validate_tree(out, member_ids=member_ids if member_ids else None)
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
                Task.deleted_at.is_(None),
                Task.status != "done",
                Task.end_date.is_not(None),
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
