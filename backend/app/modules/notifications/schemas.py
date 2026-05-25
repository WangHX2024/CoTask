from marshmallow import Schema, fields


class NotificationItem(Schema):
    id = fields.Int()
    type = fields.Str()
    payload = fields.Raw()
    read_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()


class NotifyListQuery(Schema):
    only_unread = fields.Bool(load_default=False)
    limit = fields.Int(load_default=50)


class ReadAllRequest(Schema):
    ids = fields.List(fields.Int())
