from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth
from .schemas_api import JobCreate, JobInfo
from .service import create_job, get_job

blp = Blueprint("ai", "ai", url_prefix="/api/ai", description="AI 异步任务")


@blp.route("/jobs")
class Jobs(MethodView):
    @require_auth
    @blp.arguments(JobCreate)
    @blp.response(202, JobInfo)
    def post(self, data):
        return create_job(
            current_user_id(),
            data["scope"],
            data.get("group_id"),
            data.get("payload", {}),
        )


@blp.route("/jobs/<int:job_id>")
class JobItem(MethodView):
    @require_auth
    @blp.response(200, JobInfo)
    def get(self, job_id):
        return get_job(current_user_id(), job_id)
