from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import require_group_role
from .schemas import (
    BulkTreeReplaceRequest,
    CreateNodeRequest,
    MoveNodeRequest,
    TaskNode,
    TreeResponse,
    UpdateNodeRequest,
)
from .service import (
    create_node,
    delete_node,
    get_tree,
    move_node,
    replace_tree,
    update_node,
)

blp = Blueprint("tree", "tree", url_prefix="/api/groups", description="项目树管理")


@blp.route("/<int:group_id>/tree")
class Tree(MethodView):
    @require_group_role("member")
    @blp.response(200, TreeResponse)
    def get(self, group_id):
        return get_tree(group_id)

    @require_group_role("leader")
    @blp.arguments(BulkTreeReplaceRequest)
    @blp.response(200, TreeResponse)
    def put(self, data, group_id):
        return replace_tree(group_id, g.current_user_id, data)


@blp.route("/<int:group_id>/tree/nodes")
class Nodes(MethodView):
    @require_group_role("leader")
    @blp.arguments(CreateNodeRequest)
    @blp.response(201, TaskNode)
    def post(self, data, group_id):
        return create_node(group_id, g.current_user_id, data)


@blp.route("/<int:group_id>/tree/nodes/<int:task_id>")
class Node(MethodView):
    @require_group_role("member")
    @blp.arguments(UpdateNodeRequest)
    @blp.response(200, TaskNode)
    def patch(self, data, group_id, task_id):
        # member can change own task status only — service-side checks
        return update_node(group_id, g.current_user_id, task_id, data)

    @require_group_role("leader")
    @blp.response(204)
    def delete(self, group_id, task_id):
        delete_node(group_id, g.current_user_id, task_id)
        return ""


@blp.route("/<int:group_id>/tree/nodes/<int:task_id>/move")
class Move(MethodView):
    @require_group_role("leader")
    @blp.arguments(MoveNodeRequest)
    @blp.response(204)
    def post(self, data, group_id, task_id):
        move_node(group_id, g.current_user_id, task_id, data.get("new_parent_id"), data.get("new_position"))
        return ""
