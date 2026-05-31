from marshmallow import Schema, fields, validate

from ...common.schemas import UTCDateTime


class SignRequest(Schema):
    filename = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    size = fields.Int(required=True)
    md5 = fields.Str()
    mime = fields.Str(validate=validate.Length(max=128))
    group_id = fields.Int(required=True)
    folder_id = fields.Int(load_default=0, metadata={"description": "0 or omit = group root"})
    tag_task_id = fields.Int(allow_none=True)
    task_id = fields.Int(allow_none=True, metadata={"description": "alias of tag_task_id"})
    visibility = fields.Str(load_default="group", validate=validate.OneOf(["group", "public", "self"]))


class SignResponse(Schema):
    file_id = fields.Int()
    upload_url = fields.Str(allow_none=True)
    deduped = fields.Bool()


class FinalizeRequest(Schema):
    file_id = fields.Int(required=True)


class FileInfo(Schema):
    id = fields.Int()
    filename = fields.Str()
    size = fields.Int()
    mime = fields.Str(validate=validate.Length(max=128))
    md5 = fields.Str()
    uploader_id = fields.Int()
    uploader_name = fields.Str()
    group_id = fields.Int()
    folder_id = fields.Int()
    tag_task_id = fields.Int(allow_none=True)
    tag_label = fields.Str()
    task_id = fields.Int(allow_none=True)
    visibility = fields.Str()
    version = fields.Int()
    parent_file_id = fields.Int(allow_none=True)
    download_url = fields.Str()
    created_at = UTCDateTime()


class FileTagUpdate(Schema):
    tag_task_id = fields.Int(allow_none=True)


class FileMoveBatch(Schema):
    file_ids = fields.List(
        fields.Int(),
        required=True,
        validate=validate.Length(min=1, max=200),
    )
    folder_id = fields.Int(load_default=0, metadata={"description": "0 = group root"})


class FileTagBatch(Schema):
    file_ids = fields.List(
        fields.Int(),
        required=True,
        validate=validate.Length(min=1, max=200),
    )
    tag_task_id = fields.Int(allow_none=True)


class FileBatchResult(Schema):
    updated = fields.Int()
    items = fields.Nested(FileInfo, many=True)


class FolderCreate(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    parent_id = fields.Int(allow_none=True)


class FolderRename(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))


class FolderDeleteResult(Schema):
    deleted_folders = fields.Int()
    deleted_files = fields.Int()


class FolderInfo(Schema):
    id = fields.Int()
    name = fields.Str()
    parent_id = fields.Int(allow_none=True)
    path = fields.Str()


class FileListQuery(Schema):
    folder_id = fields.Int(allow_none=True)
    folder_root = fields.Bool(load_default=False)
    tag_task_id = fields.Int(allow_none=True)
    tag_uncategorized = fields.Bool(load_default=False)
