from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import require_group_role
from .schemas import (
    BulkTreeReplaceRequest,
    CreateNodeRequest,
    GrantNodeManagerRequest,
    MoveNodeRequest,
    NodeManagerInfo,
    NodePatchResponse,
    TaskNode,
    TreeResponse,
    UpdateNodeRequest,
)
from ..inspiration.schemas import RelatedInspirationResponse
from .service import (
    add_node_manager,
    create_node,
    delete_node,
    get_node_managers,
    get_related_inspiration,
    get_tree,
    move_node,
    remove_node_manager,
    replace_tree,
    update_node,
)

blp = Blueprint("tree", "tree", url_prefix="/api/groups", description="项目树管理")


@blp.route("/<int:group_id>/tree")
class Tree(MethodView):
    @require_group_role("member")
    @blp.response(200, TreeResponse)
    def get(self, group_id):
        return get_tree(group_id, g.current_user_id)

    @require_group_role("leader")
    @blp.arguments(BulkTreeReplaceRequest)
    @blp.response(200, TreeResponse)
    def put(self, data, group_id):
        return replace_tree(group_id, g.current_user_id, data)


@blp.route("/<int:group_id>/tree/nodes")
class Nodes(MethodView):
    @require_group_role("member")
    @blp.arguments(CreateNodeRequest)
    @blp.response(201, TaskNode)
    def post(self, data, group_id):
        return create_node(group_id, g.current_user_id, data)


@blp.route("/<int:group_id>/tree/nodes/<int:task_id>")
class Node(MethodView):
    @require_group_role("member")
    @blp.arguments(UpdateNodeRequest)
    @blp.response(200, NodePatchResponse)
    def patch(self, data, group_id, task_id):
        # member can change own task status only — service-side checks
        return update_node(group_id, g.current_user_id, task_id, data)

    @require_group_role("member")
    @blp.response(204)
    def delete(self, group_id, task_id):
        delete_node(group_id, g.current_user_id, task_id)
        return ""


@blp.route("/<int:group_id>/tree/nodes/<int:task_id>/related-inspiration")
class RelatedInspiration(MethodView):
    @require_group_role("member")
    @blp.response(200, RelatedInspirationResponse)
    def get(self, group_id, task_id):
        return get_related_inspiration(group_id, task_id, g.current_user_id)


@blp.route("/<int:group_id>/tree/nodes/<int:task_id>/managers")
class NodeManagers(MethodView):
    @require_group_role("member")
    @blp.response(200, NodeManagerInfo(many=True))
    def get(self, group_id, task_id):
        return get_node_managers(group_id, task_id)

    @require_group_role("member")
    @blp.arguments(GrantNodeManagerRequest)
    @blp.response(201, NodeManagerInfo)
    def post(self, data, group_id, task_id):
        return add_node_manager(group_id, g.current_user_id, task_id, data["user_id"])


@blp.route("/<int:group_id>/tree/nodes/<int:task_id>/managers/<int:user_id>")
class NodeManagerItem(MethodView):
    @require_group_role("member")
    @blp.response(204)
    def delete(self, group_id, task_id, user_id):
        remove_node_manager(group_id, g.current_user_id, task_id, user_id)
        return ""


@blp.route("/<int:group_id>/tree/nodes/<int:task_id>/move")
class Move(MethodView):
    @require_group_role("member")
    @blp.arguments(MoveNodeRequest)
    @blp.response(204)
    def post(self, data, group_id, task_id):
        move_node(group_id, g.current_user_id, task_id, data.get("new_parent_id"), data.get("new_position"))
        return ""
