from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from ...common.permissions import current_user_id, require_auth, require_group_role
from .schemas import (
    FileBatchResult,
    FileInfo,
    FileListQuery,
    FileMoveBatch,
    FileTagBatch,
    FileTagUpdate,
    FinalizeRequest,
    FolderCreate,
    FolderDeleteResult,
    FolderInfo,
    FolderRename,
    SignRequest,
    SignResponse,
)
from .service import (
    bulk_update_file_tags,
    create_folder,
    delete_file,
    delete_folder,
    finalize,
    list_files,
    list_folders,
    move_files,
    rename_folder,
    sign_upload,
    update_file_tag,
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

    @require_auth
    @blp.arguments(FileTagUpdate)
    @blp.response(200, FileInfo)
    def patch(self, data, file_id):
        return update_file_tag(current_user_id(), file_id, data.get("tag_task_id"))


@blp.route("/groups/<int:group_id>/files/move")
class GroupFilesMove(MethodView):
    @require_group_role("member")
    @blp.arguments(FileMoveBatch)
    @blp.response(200, FileBatchResult)
    def post(self, data, group_id):
        return move_files(
            g.current_user_id,
            group_id,
            data["file_ids"],
            data.get("folder_id", 0),
        )


@blp.route("/groups/<int:group_id>/files/tags")
class GroupFilesTagBatch(MethodView):
    @require_group_role("member")
    @blp.arguments(FileTagBatch)
    @blp.response(200, FileBatchResult)
    def post(self, data, group_id):
        return bulk_update_file_tags(
            g.current_user_id,
            group_id,
            data["file_ids"],
            data.get("tag_task_id"),
        )


@blp.route("/groups/<int:group_id>/files")
class GroupFiles(MethodView):
    @require_group_role("member")
    @blp.arguments(FileListQuery, location="query")
    @blp.response(200, FileInfo(many=True))
    def get(self, query, group_id):
        return list_files(
            g.current_user_id,
            group_id,
            folder_id=query.get("folder_id"),
            folder_root=query.get("folder_root") or False,
            tag_task_id=query.get("tag_task_id"),
            tag_uncategorized=query.get("tag_uncategorized") or False,
        )


@blp.route("/groups/<int:group_id>/folders")
class GroupFolders(MethodView):
    @require_group_role("member")
    @blp.response(200, FolderInfo(many=True))
    def get(self, group_id):
        return list_folders(g.current_user_id, group_id)

    @require_group_role("member")
    @blp.arguments(FolderCreate)
    @blp.response(201, FolderInfo)
    def post(self, data, group_id):
        return create_folder(g.current_user_id, group_id, data["name"], data.get("parent_id"))


@blp.route("/groups/<int:group_id>/folders/<int:folder_id>")
class GroupFolderItem(MethodView):
    @require_group_role("member")
    @blp.arguments(FolderRename)
    @blp.response(200, FolderInfo)
    def patch(self, data, group_id, folder_id):
        return rename_folder(g.current_user_id, group_id, folder_id, data["name"])

    @require_group_role("member")
    @blp.response(200, FolderDeleteResult)
    def delete(self, group_id, folder_id):
        return delete_folder(g.current_user_id, group_id, folder_id)
