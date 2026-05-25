from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import require_group_role
from .schemas import TimelineQuery, TimelineResponse
from .service import get_timeline

blp = Blueprint("timeline", "timeline", url_prefix="/api/groups", description="时间轴 / 甘特图")


@blp.route("/<int:group_id>/timeline")
class Timeline(MethodView):
    @require_group_role("member")
    @blp.arguments(TimelineQuery, location="query")
    @blp.response(200, TimelineResponse)
    def get(self, query, group_id):
        return get_timeline(group_id, query.get("view", "week"), query.get("start"))
