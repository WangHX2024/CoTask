from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth
from .schemas import AdviceRefreshResponse, AdviceResponse, DashOverviewResponse, DashResponse
from .service import get_daily_advice, get_dashboard, get_overview, refresh_daily_advice_job

blp = Blueprint("dashboard", "dashboard", url_prefix="/api/dashboard", description="个人首页聚合")


@blp.route("/overview")
class Overview(MethodView):
    @require_auth
    @blp.response(200, DashOverviewResponse)
    def get(self):
        include = request.args.get("include_advice", "true").lower() not in ("0", "false", "no")
        return get_overview(current_user_id(), include_advice=include)


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


@blp.route("/advice/refresh")
class AdviceRefresh(MethodView):
    @require_auth
    @blp.response(202, AdviceRefreshResponse)
    def post(self):
        job_id = refresh_daily_advice_job(current_user_id())
        return {"job_id": job_id, "status": "pending"}
