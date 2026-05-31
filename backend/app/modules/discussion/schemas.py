from marshmallow import Schema, fields, validate

from ...common.schemas import UTCDateTime


class ChannelCreate(Schema):
    name = fields.Str(load_default="", validate=validate.Length(max=256))
    task_id = fields.Int(allow_none=True, load_default=None)


class ChannelInfo(Schema):
    id = fields.Int()
    name = fields.Str()
    task_id = fields.Int(allow_none=True)
    created_by = fields.Int()
    created_at = UTCDateTime()


class MessageCreate(Schema):
    body = fields.Str(required=True, validate=validate.Length(min=1, max=4000))
    channel_id = fields.Int(allow_none=True)
    task_id = fields.Int(allow_none=True)
    anon = fields.Bool(load_default=False)
    quote_id = fields.Int(allow_none=True)


class MessageInfo(Schema):
    id = fields.Int()
    channel_id = fields.Int(allow_none=True)
    task_id = fields.Int(allow_none=True)
    body = fields.Str()
    author_id = fields.Int()
    author_name = fields.Str()
    author_avatar = fields.Str()
    anon = fields.Bool()
    quote_id = fields.Int(allow_none=True)
    created_at = UTCDateTime()


class MessageQuery(Schema):
    channel_id = fields.Int(allow_none=True)
    task_id = fields.Int(allow_none=True)
    limit = fields.Int(load_default=50)
    before_id = fields.Int(allow_none=True)
