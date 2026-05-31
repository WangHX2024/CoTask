from marshmallow import Schema, fields


class TimelineQuery(Schema):
    view = fields.Str(load_default="week")
    start = fields.Date(allow_none=True)


class GanttBlock(Schema):
    task_id = fields.Int()
    title = fields.Str()
    title_path = fields.Str()
    user_id = fields.Int()
    user_name = fields.Str()
    user_avatar = fields.Str()
    start_date = fields.Date()
    end_date = fields.Date()
    status = fields.Str()
    progress = fields.Int()
    urgent = fields.Bool()
    dependencies = fields.List(fields.Int())


class GroupRow(Schema):
    user_id = fields.Int()
    name = fields.Str()
    avatar_url = fields.Str()
    role = fields.Str()
    blocks = fields.List(fields.Nested(GanttBlock))


class TimelineResponse(Schema):
    view = fields.Str()
    start = fields.Date()
    end = fields.Date()
    rows = fields.List(fields.Nested(GroupRow))
