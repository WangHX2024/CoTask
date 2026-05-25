from marshmallow import Schema, fields, validate


class StatusChangeRequest(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(
        ["todo", "in_progress", "done", "blocked"]
    ))


class NudgeRequest(Schema):
    message = fields.Str(load_default="加把劲！这个任务快到 DDL 了")


class AssignRequest(Schema):
    assignees = fields.List(fields.Int(), required=True)


class TaskDetail(Schema):
    id = fields.Int()
    group_id = fields.Int()
    parent_id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    is_leaf = fields.Bool()
    refined = fields.Bool()
    start_date = fields.Date()
    end_date = fields.Date()
    status = fields.Str()
    progress = fields.Int()
    assignees = fields.List(fields.Int())
    dependencies = fields.List(fields.Int())
    inspiration_post_ids = fields.List(fields.Int())
    path = fields.Str()
    depth = fields.Int()
    version = fields.Int()
