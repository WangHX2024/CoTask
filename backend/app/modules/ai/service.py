from __future__ import annotations

from ...common.errors import BadRequest, Forbidden, NotFound
from ...common.permissions import get_group_role
from ...common.tx import tx
from ...extensions import db
from ...models import AiConversation


def create_job(uid: int, scope: str, group_id: int | None, payload: dict) -> AiConversation:
    if group_id:
        role = get_group_role(uid, group_id)
        if not role:
            raise Forbidden("非小组成员")
        if scope in ("tree_gen", "tree_edit", "assignment") and role != "leader":
            raise Forbidden("仅组长可执行")
    with tx() as s:
        c = AiConversation(scope=scope, group_id=group_id, user_id=uid, context=payload, status="pending")
        s.add(c)
        s.flush()
    # enqueue celery task
    from ...tasks.ai_tasks import run_ai_job
    run_ai_job.delay(c.id)
    return c


def get_job(uid: int, job_id: int) -> AiConversation:
    c = db.session.get(AiConversation, job_id)
    if not c or c.user_id != uid:
        raise NotFound("job")
    return c
