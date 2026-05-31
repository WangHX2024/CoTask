from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.errors import NotFound
from ...common.permissions import require_group_role
from ...extensions import db
from ...models import DiscussionChannel
from .schemas import (
    ChannelCreate,
    ChannelInfo,
    MessageCreate,
    MessageInfo,
    MessageQuery,
)
from .service import (
    channel_message_count,
    create_channel,
    get_or_create_task_channel,
    list_channels,
    list_messages,
    post_message,
)

blp = Blueprint("discussion", "discussion", url_prefix="/api/groups", description="小组讨论")


@blp.route("/<int:group_id>/discussion/channels")
class Channels(MethodView):
    @require_group_role("member")
    @blp.response(200, ChannelInfo(many=True))
    def get(self, group_id):
        return list_channels(group_id, g.current_user_id)

    @require_group_role("member")
    @blp.arguments(ChannelCreate)
    @blp.response(201, ChannelInfo)
    def post(self, data, group_id):
        return create_channel(
            g.current_user_id,
            group_id,
            data.get("name") or "",
            task_id=data.get("task_id"),
        )


@blp.route("/<int:group_id>/discussion/channels/task/<int:task_id>")
class TaskChannel(MethodView):
    @require_group_role("member")
    @blp.response(200, ChannelInfo)
    def post(self, group_id, task_id):
        return get_or_create_task_channel(g.current_user_id, group_id, task_id)


@blp.route("/<int:group_id>/discussion/channels/<int:channel_id>/stats")
class ChannelStats(MethodView):
    @require_group_role("member")
    def get(self, group_id, channel_id):
        ch = db.session.get(DiscussionChannel, channel_id)
        if not ch or ch.group_id != group_id:
            raise NotFound("channel")
        return {"message_count": channel_message_count(channel_id)}


@blp.route("/<int:group_id>/discussion/messages")
class Messages(MethodView):
    @require_group_role("member")
    @blp.arguments(MessageQuery, location="query")
    @blp.response(200, MessageInfo(many=True))
    def get(self, query, group_id):
        return list_messages(
            g.current_user_id, group_id,
            channel_id=query.get("channel_id"),
            task_id=query.get("task_id"),
            limit=query.get("limit", 50),
            before_id=query.get("before_id"),
        )

    @require_group_role("member")
    @blp.arguments(MessageCreate)
    @blp.response(201, MessageInfo)
    def post(self, data, group_id):
        return post_message(g.current_user_id, group_id, data)
