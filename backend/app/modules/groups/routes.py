from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth, require_group_role
from .schemas import (
    DissolveRequest,
    GroupBrief,
    GroupCreate,
    GroupUpdate,
    JoinRequest,
    MemberInfo,
    TransferRequest,
)
from .service import (
    create_group,
    dissolve_group,
    get_group,
    join_group,
    kick_member,
    leave_group,
    list_members,
    list_my_groups,
    transfer_leader,
    update_group,
)

blp = Blueprint("groups", "groups", url_prefix="/api/groups", description="小组与成员管理")


@blp.route("")
class GroupsCollection(MethodView):
    @require_auth
    @blp.response(200, GroupBrief(many=True))
    def get(self):
        return list_my_groups(current_user_id())

    @require_auth
    @blp.arguments(GroupCreate)
    @blp.response(201, GroupBrief)
    def post(self, data):
        grp = create_group(current_user_id(), data)
        return get_group(current_user_id(), grp.id)


@blp.route("/join")
class Join(MethodView):
    @require_auth
    @blp.arguments(JoinRequest)
    @blp.response(200, GroupBrief)
    def post(self, data):
        return join_group(current_user_id(), data["invite_code"])


@blp.route("/<int:group_id>")
class GroupDetail(MethodView):
    @require_group_role("member")
    @blp.response(200, GroupBrief)
    def get(self, group_id):
        return get_group(g.current_user_id, group_id)

    @require_group_role("leader")
    @blp.arguments(GroupUpdate)
    @blp.response(200, GroupBrief)
    def patch(self, data, group_id):
        return update_group(g.current_user_id, group_id, data)

    @require_group_role("leader")
    @blp.arguments(DissolveRequest)
    @blp.response(204)
    def delete(self, data, group_id):
        dissolve_group(g.current_user_id, group_id, data["confirm_name"])
        return ""


@blp.route("/<int:group_id>/members")
class Members(MethodView):
    @require_group_role("member")
    @blp.response(200, MemberInfo(many=True))
    def get(self, group_id):
        return list_members(group_id)


@blp.route("/<int:group_id>/members/<int:uid>")
class MemberItem(MethodView):
    @require_group_role("leader")
    @blp.response(204)
    def delete(self, group_id, uid):
        kick_member(g.current_user_id, group_id, uid)
        return ""


@blp.route("/<int:group_id>/transfer")
class Transfer(MethodView):
    @require_group_role("leader")
    @blp.arguments(TransferRequest)
    @blp.response(204)
    def post(self, data, group_id):
        transfer_leader(g.current_user_id, group_id, data["target_user_id"])
        return ""


@blp.route("/<int:group_id>/leave")
class Leave(MethodView):
    @require_group_role("member")
    @blp.response(204)
    def post(self, group_id):
        leave_group(g.current_user_id, group_id)
        return ""
