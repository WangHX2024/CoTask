from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth
from .schemas import AdviceResponse, DashResponse
from .service import get_daily_advice, get_dashboard

blp = Blueprint("dashboard", "dashboard", url_prefix="/api/dashboard", description="个人首页聚合")


@blp.route("/tasks")
class Tasks(MethodView):
    @require_auth
    @blp.response(200, DashResponse)
    def get(self):
        return get_dashboard(current_user_id())


@blp.route("/advice")
class Advice(MethodView):
    @require_auth
    @blp.response(200, AdviceResponse)
    def get(self):
        return get_daily_advice(current_user_id())
