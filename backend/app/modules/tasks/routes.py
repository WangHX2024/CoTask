from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import require_group_role
from .schemas import AssignRequest, NudgeRequest, StatusChangeRequest, TaskDetail
from .service import assign, change_status, get_detail, nudge

blp = Blueprint("tasks", "tasks", url_prefix="/api/groups", description="原子任务操作")


@blp.route("/<int:group_id>/tasks/<int:task_id>")
class Detail(MethodView):
    @require_group_role("member")
    @blp.response(200, TaskDetail)
    def get(self, group_id, task_id):
        return get_detail(group_id, task_id)


@blp.route("/<int:group_id>/tasks/<int:task_id>/status")
class Status(MethodView):
    @require_group_role("member")
    @blp.arguments(StatusChangeRequest)
    @blp.response(200, TaskDetail)
    def patch(self, data, group_id, task_id):
        return change_status(g.current_user_id, group_id, task_id, data["status"], g.current_role)


@blp.route("/<int:group_id>/tasks/<int:task_id>/assign")
class Assign(MethodView):
    @require_group_role("leader")
    @blp.arguments(AssignRequest)
    @blp.response(200, TaskDetail)
    def post(self, data, group_id, task_id):
        return assign(g.current_user_id, group_id, task_id, data["assignees"])


@blp.route("/<int:group_id>/tasks/<int:task_id>/nudge")
class Nudge(MethodView):
    @require_group_role("member")
    @blp.arguments(NudgeRequest)
    @blp.response(204)
    def post(self, data, group_id, task_id):
        nudge(g.current_user_id, group_id, task_id, data.get("message", ""))
        return ""
