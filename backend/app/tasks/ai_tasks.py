"""Celery: run AI jobs, push results via WS."""
from __future__ import annotations

import logging
import traceback

from ..common.tx import tx
from ..extensions import celery, db
from ..models import AiConversation
from ..modules.ai.runner import (
    run_assignment,
    run_daily_advice,
    run_tree_edit,
    run_tree_gen,
)
from ..modules.notifications.service import push_user

log = logging.getLogger(__name__)


@celery.task(name="cotask.ai.run", bind=True, max_retries=1)
def run_ai_job(self, conversation_id: int):
    conv = db.session.get(AiConversation, conversation_id)
    if not conv:
        log.warning("AI job %s: conversation missing", conversation_id)
        return

    with tx():
        conv.status = "streaming"
    push_user(conv.user_id, "ai.job_progress", {
        "job_id": conv.id, "status": "streaming",
    })

    try:
        scope = conv.scope
        ctx = conv.context or {}
        if scope == "tree_gen":
            result = run_tree_gen(conv, ctx.get("document", ""))
        elif scope == "tree_edit":
            result = run_tree_edit(conv, ctx.get("current_tree", {}), ctx.get("instruction", ""))
        elif scope == "daily_advice":
            result = run_daily_advice(conv, ctx)
        elif scope == "assignment":
            result = run_assignment(conv, ctx.get("tasks", []))
        else:
            raise ValueError(f"unsupported scope {scope}")

        with tx():
            conv.status = "done"
            conv.result = result
        push_user(conv.user_id, "ai.job_progress", {
            "job_id": conv.id, "status": "done", "result": result,
        })
    except Exception as e:
        log.error("AI job %s failed: %s\n%s", conversation_id, e, traceback.format_exc())
        with tx():
            conv.status = "failed"
            conv.error = str(e)
        push_user(conv.user_id, "ai.job_progress", {
            "job_id": conv.id, "status": "failed", "error": str(e),
        })
