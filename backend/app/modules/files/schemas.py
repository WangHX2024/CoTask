from marshmallow import Schema, fields, validate


class SignRequest(Schema):
    filename = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    size = fields.Int(required=True)
    md5 = fields.Str()
    mime = fields.Str()
    group_id = fields.Int(allow_none=True)
    task_id = fields.Int(allow_none=True)
    folder_id = fields.Int(allow_none=True)
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
    mime = fields.Str()
    md5 = fields.Str()
    uploader_id = fields.Int()
    uploader_name = fields.Str()
    group_id = fields.Int()
    task_id = fields.Int()
    folder_id = fields.Int()
    visibility = fields.Str()
    version = fields.Int()
    parent_file_id = fields.Int(allow_none=True)
    download_url = fields.Str()
    created_at = fields.DateTime()


class FolderCreate(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    parent_id = fields.Int(allow_none=True)


class FolderInfo(Schema):
    id = fields.Int()
    name = fields.Str()
    parent_id = fields.Int(allow_none=True)
    path = fields.Str()


class FileListQuery(Schema):
    task_id = fields.Int(allow_none=True)
    folder_id = fields.Int(allow_none=True)
