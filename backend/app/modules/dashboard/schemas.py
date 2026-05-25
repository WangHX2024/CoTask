from marshmallow import Schema, fields


class DashTask(Schema):
    task_id = fields.Int()
    title = fields.Str()
    group_id = fields.Int()
    group_name = fields.Str()
    course_name = fields.Str()
    end_date = fields.Date()
    status = fields.Str()
    progress = fields.Int()
    urgent = fields.Bool()
    days_left = fields.Int()


class LeaderGroup(Schema):
    group_id = fields.Int()
    course_name = fields.Str()
    name = fields.Str()
    progress = fields.Int()
    todo = fields.Int()
    in_progress = fields.Int()
    done = fields.Int()
    blocked = fields.Int()
    urgent_count = fields.Int()


class DashResponse(Schema):
    tasks = fields.List(fields.Nested(DashTask))
    urgent = fields.List(fields.Nested(DashTask))
    leader_groups = fields.List(fields.Nested(LeaderGroup))


class AdviceResponse(Schema):
    advice = fields.Str()
    suggestions = fields.List(fields.Str())
    generated_at = fields.DateTime()
    cached = fields.Bool()
