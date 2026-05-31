from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth
from .schemas_api import AiMessageInfo, JobCreate, JobInfo
from .service import create_job, get_job, list_messages

blp = Blueprint("ai", "ai", url_prefix="/api/ai", description="AI 异步任务")


def _parse_job_request(data: dict) -> tuple[dict, int | None]:
    """conversation_id may be top-level (new API) or inside payload (compat)."""
    payload = dict(data.get("payload") or {})
    conv_id = data.get("conversation_id")
    if conv_id is None and payload.get("conversation_id") is not None:
        try:
            conv_id = int(payload.pop("conversation_id"))
        except (TypeError, ValueError):
            conv_id = None
    else:
        payload.pop("conversation_id", None)
    return payload, conv_id


@blp.route("/jobs")
class Jobs(MethodView):
    @require_auth
    @blp.arguments(JobCreate)
    @blp.response(202, JobInfo)
    def post(self, data):
        payload, conv_id = _parse_job_request(data)
        return create_job(
            current_user_id(),
            data["scope"],
            data.get("group_id"),
            payload,
            conv_id,
        )


@blp.route("/jobs/<int:job_id>")
class JobItem(MethodView):
    @require_auth
    @blp.response(200, JobInfo)
    def get(self, job_id):
        return get_job(current_user_id(), job_id)


@blp.route("/jobs/<int:job_id>/messages")
class JobMessages(MethodView):
    @require_auth
    @blp.response(200, AiMessageInfo(many=True))
    def get(self, job_id):
        return list_messages(current_user_id(), job_id)
