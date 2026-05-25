from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth, require_group_role
from .schemas import (
    FileInfo,
    FileListQuery,
    FinalizeRequest,
    FolderCreate,
    FolderInfo,
    SignRequest,
    SignResponse,
)
from .service import (
    create_folder,
    delete_file,
    finalize,
    list_files,
    list_folders,
    sign_upload,
)

blp = Blueprint("files", "files", url_prefix="/api", description="文件 / 附件")


@blp.route("/files/sign")
class Sign(MethodView):
    @require_auth
    @blp.arguments(SignRequest)
    @blp.response(200, SignResponse)
    def post(self, data):
        return sign_upload(current_user_id(), data)


@blp.route("/files/finalize")
class Finalize(MethodView):
    @require_auth
    @blp.arguments(FinalizeRequest)
    @blp.response(200, FileInfo)
    def post(self, data):
        return finalize(current_user_id(), data["file_id"])


@blp.route("/files/<int:file_id>")
class FileItem(MethodView):
    @require_auth
    @blp.response(204)
    def delete(self, file_id):
        delete_file(current_user_id(), file_id)
        return ""


@blp.route("/groups/<int:group_id>/files")
class GroupFiles(MethodView):
    @require_group_role("member")
    @blp.arguments(FileListQuery, location="query")
    @blp.response(200, FileInfo(many=True))
    def get(self, query, group_id):
        return list_files(
            g.current_user_id, group_id,
            task_id=query.get("task_id"),
            folder_id=query.get("folder_id"),
        )


@blp.route("/groups/<int:group_id>/folders")
class GroupFolders(MethodView):
    @require_group_role("member")
    @blp.response(200, FolderInfo(many=True))
    def get(self, group_id):
        return list_folders(g.current_user_id, group_id)

    @require_group_role("leader")
    @blp.arguments(FolderCreate)
    @blp.response(201, FolderInfo)
    def post(self, data, group_id):
        return create_folder(g.current_user_id, group_id, data["name"], data.get("parent_id"))
