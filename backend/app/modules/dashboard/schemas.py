from marshmallow import Schema, fields

from ...common.schemas import UTCDateTime


class AssigneeBrief(Schema):
    user_id = fields.Int()
    name = fields.Str()
    avatar_url = fields.Str(allow_none=True)


class DashTask(Schema):
    task_id = fields.Int()
    title = fields.Str()
    title_path = fields.Str()
    group_id = fields.Int()
    group_name = fields.Str()
    course_name = fields.Str()
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    status = fields.Str()
    progress = fields.Int()
    has_children = fields.Bool()
    urgent = fields.Bool()
    urgency_level = fields.Str(allow_none=True)
    days_left = fields.Int()
    assignees = fields.List(fields.Nested(AssigneeBrief))


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
    due_soon_count = fields.Int()
    unassigned_count = fields.Int()


class DashFocus(Schema):
    open_count = fields.Int()
    critical_count = fields.Int()
    warning_count = fields.Int()


class AdviceResponse(Schema):
    advice = fields.Str()
    suggestions = fields.List(fields.Str())
    generated_at = UTCDateTime()
    cached = fields.Bool()


class DashResponse(Schema):
    tasks = fields.List(fields.Nested(DashTask))
    unscheduled = fields.List(fields.Nested(DashTask))
    urgent = fields.List(fields.Nested(DashTask))
    urgent_warning = fields.List(fields.Nested(DashTask))
    leader_groups = fields.List(fields.Nested(LeaderGroup))
    focus = fields.Nested(DashFocus)


class DashOverviewResponse(DashResponse):
    advice = fields.Nested(AdviceResponse, allow_none=True)


class AdviceRefreshResponse(Schema):
    job_id = fields.Int()
    status = fields.Str()
