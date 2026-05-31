from __future__ import annotations

from sqlalchemy import select

from ...common.errors import BadRequest, Conflict, Forbidden, NotFound
from ...common.json_util import json_safe
from ...common.permissions import get_group_role
from ...common.tx import tx
from ...extensions import db
from ...models import AiConversation, AiMessage

TREE_CHAT_SCOPES = frozenset({"tree_gen", "tree_edit"})


def create_job(
    uid: int,
    scope: str,
    group_id: int | None,
    payload: dict,
    conversation_id: int | None = None,
) -> AiConversation:
    if conversation_id:
        return _continue_job(uid, conversation_id, scope, group_id, payload)
    return _start_job(uid, scope, group_id, payload)


def _start_job(uid: int, scope: str, group_id: int | None, payload: dict) -> AiConversation:
    if group_id:
        role = get_group_role(uid, group_id)
        if not role:
            raise Forbidden("非小组成员")
        if scope in ("tree_gen", "tree_edit", "assignment") and role != "leader":
            raise Forbidden("仅组长可执行")

    ctx = dict(payload or {})
    if scope == "tree_gen":
        document = (ctx.get("document") or "").strip()
        if not document:
            raise BadRequest("INVALID_PAYLOAD", "请提供课程要求或项目描述")
        ctx = {"document": document[:8000]}
    elif scope == "tree_edit":
        instruction = (ctx.get("instruction") or "").strip()
        if not instruction:
            raise BadRequest("INVALID_PAYLOAD", "请提供编辑指令")
        if not ctx.get("current_tree"):
            raise BadRequest("INVALID_PAYLOAD", "缺少当前项目树")
        ctx = {
            "current_tree": ctx["current_tree"],
            "instruction": instruction,
        }

    with tx() as s:
        c = AiConversation(
            scope=scope,
            group_id=group_id,
            user_id=uid,
            context=json_safe(ctx),
            status="pending",
        )
        s.add(c)
        s.flush()
    _enqueue(c.id)
    return c


def _continue_job(
    uid: int,
    conversation_id: int,
    scope: str,
    group_id: int | None,
    payload: dict,
) -> AiConversation:
    if scope not in TREE_CHAT_SCOPES:
        raise BadRequest("INVALID_SCOPE", "此任务类型不支持多轮对话")

    c = db.session.get(AiConversation, conversation_id)
    if not c or c.user_id != uid:
        raise NotFound("job")
    if c.scope != scope:
        raise BadRequest("SCOPE_MISMATCH", "会话类型不一致")
    if group_id is not None and c.group_id != group_id:
        raise BadRequest("GROUP_MISMATCH", "小组不一致")
    if c.status in ("pending", "streaming"):
        raise Conflict("JOB_RUNNING", "上一轮仍在处理中，请稍候")

    instruction = (payload.get("instruction") or payload.get("document") or "").strip()
    if not instruction:
        raise BadRequest("INVALID_PAYLOAD", "请输入本轮指令")

    if group_id:
        role = get_group_role(uid, group_id)
        if not role:
            raise Forbidden("非小组成员")
        if role != "leader":
            raise Forbidden("仅组长可执行")

    with tx():
        ctx = dict(c.context or {})
        ctx["instruction"] = instruction
        if scope == "tree_gen" and payload.get("document"):
            ctx["document"] = str(payload["document"])[:8000]
        c.context = json_safe(ctx)
        c.status = "pending"
        c.error = None

    _enqueue(c.id)
    return c


def get_job(uid: int, job_id: int) -> AiConversation:
    c = db.session.get(AiConversation, job_id)
    if not c or c.user_id != uid:
        raise NotFound("job")
    return c


def list_messages(uid: int, job_id: int) -> list[dict]:
    c = get_job(uid, job_id)
    rows = db.session.execute(
        select(AiMessage)
        .where(AiMessage.conversation_id == c.id, AiMessage.role.in_(["user", "assistant"]))
        .order_by(AiMessage.id)
    ).scalars().all()
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at,
        }
        for m in rows
    ]


def _enqueue(conversation_id: int) -> None:
    from ...tasks.ai_tasks import run_ai_job

    run_ai_job.delay(conversation_id)
