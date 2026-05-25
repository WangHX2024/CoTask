from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth
from .schemas import (
    CommentBrief,
    CommentCreate,
    ListResponse,
    PostCreate,
    PostDetail,
    PostQuery,
    PostUpdate,
    TemplateImportRequest,
)
from .service import (
    add_comment,
    create_post,
    delete_post,
    get_post,
    import_template,
    list_comments,
    list_posts,
    toggle_favorite,
    toggle_like,
    update_post,
)

blp = Blueprint("inspiration", "inspiration", url_prefix="/api/inspiration", description="灵感广场")


@blp.route("/posts")
class Posts(MethodView):
    @require_auth
    @blp.arguments(PostQuery, location="query")
    @blp.response(200, ListResponse)
    def get(self, query):
        return list_posts(current_user_id(), query)

    @require_auth
    @blp.arguments(PostCreate)
    @blp.response(201, PostDetail)
    def post(self, data):
        return create_post(current_user_id(), data)


@blp.route("/posts/<int:post_id>")
class PostItem(MethodView):
    @require_auth
    @blp.response(200, PostDetail)
    def get(self, post_id):
        return get_post(current_user_id(), post_id)

    @require_auth
    @blp.arguments(PostUpdate)
    @blp.response(200, PostDetail)
    def patch(self, data, post_id):
        return update_post(current_user_id(), post_id, data)

    @require_auth
    @blp.response(204)
    def delete(self, post_id):
        delete_post(current_user_id(), post_id)
        return ""


@blp.route("/posts/<int:post_id>/like")
class Like(MethodView):
    @require_auth
    @blp.response(200)
    def post(self, post_id):
        return {"liked": toggle_like(current_user_id(), post_id)}


@blp.route("/posts/<int:post_id>/favorite")
class Favorite(MethodView):
    @require_auth
    @blp.response(200)
    def post(self, post_id):
        return {"favored": toggle_favorite(current_user_id(), post_id)}


@blp.route("/posts/<int:post_id>/comments")
class Comments(MethodView):
    @require_auth
    @blp.response(200, CommentBrief(many=True))
    def get(self, post_id):
        return list_comments(post_id)

    @require_auth
    @blp.arguments(CommentCreate)
    @blp.response(201, CommentBrief)
    def post(self, data, post_id):
        return add_comment(current_user_id(), post_id, data)


@blp.route("/posts/<int:post_id>/import")
class Import(MethodView):
    @require_auth
    @blp.arguments(TemplateImportRequest)
    @blp.response(200)
    def post(self, data, post_id):
        return import_template(current_user_id(), post_id, data["to_group_id"], data.get("mode", "replace"))
