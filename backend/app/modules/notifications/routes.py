from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth
from .schemas import NotificationItem, NotifyListQuery, ReadAllRequest
from .service import clear_all, list_notifications, mark_read, unread_count

blp = Blueprint("notifications", "notifications", url_prefix="/api/notifications", description="通知中心")


@blp.route("")
class List(MethodView):
    @require_auth
    @blp.arguments(NotifyListQuery, location="query")
    @blp.response(200, NotificationItem(many=True))
    def get(self, query):
        return list_notifications(current_user_id(),
                                  only_unread=bool(query.get("only_unread")),
                                  limit=int(query.get("limit") or 50))


@blp.route("/unread-count")
class UnreadCount(MethodView):
    @require_auth
    @blp.response(200)
    def get(self):
        return {"count": unread_count(current_user_id())}


@blp.route("/read")
class ReadAll(MethodView):
    @require_auth
    @blp.arguments(ReadAllRequest)
    @blp.response(204)
    def post(self, data):
        mark_read(current_user_id(), data.get("ids") or None)
        return ""


@blp.route("/clear")
class ClearAll(MethodView):
    @require_auth
    @blp.response(204)
    def post(self):
        clear_all(current_user_id())
        return ""
