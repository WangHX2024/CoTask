from marshmallow import Schema, fields

from ...common.schemas import UTCDateTime


class NotificationItem(Schema):
    id = fields.Int()
    type = fields.Str()
    payload = fields.Raw()
    read_at = UTCDateTime(allow_none=True)
    created_at = UTCDateTime()


class NotifyListQuery(Schema):
    only_unread = fields.Bool(load_default=False)
    limit = fields.Int(load_default=50)


class ReadAllRequest(Schema):
    ids = fields.List(fields.Int())
