from marshmallow import Schema, fields, validate


class TaskNode(Schema):
    id = fields.Int()
    parent_id = fields.Int(allow_none=True)
    title = fields.Str()
    description = fields.Str()
    is_leaf = fields.Bool()
    refined = fields.Bool()
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    status = fields.Str()
    progress = fields.Int()
    depth = fields.Int()
    position = fields.Int()
    path = fields.Str()
    assignees = fields.List(fields.Int())
    dependencies = fields.List(fields.Int())
    version = fields.Int()


class TreeResponse(Schema):
    group_id = fields.Int()
    version = fields.Int()
    nodes = fields.List(fields.Nested(TaskNode))


class CreateNodeRequest(Schema):
    parent_id = fields.Int(allow_none=True, load_default=None)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    description = fields.Str(load_default="")
    is_leaf = fields.Bool(load_default=False)
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    assignees = fields.List(fields.Int(), load_default=[])
    position = fields.Int(load_default=None, allow_none=True)


class UpdateNodeRequest(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=256))
    description = fields.Str()
    is_leaf = fields.Bool()
    refined = fields.Bool()
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    status = fields.Str(validate=validate.OneOf(["todo", "in_progress", "done", "blocked"]))
    assignees = fields.List(fields.Int())
    dependencies = fields.List(fields.Int())
    expected_version = fields.Int()


class MoveNodeRequest(Schema):
    new_parent_id = fields.Int(allow_none=True, load_default=None)
    new_position = fields.Int(load_default=None, allow_none=True)


class StatusChangeRequest(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(
        ["todo", "in_progress", "done", "blocked"]
    ))


class BulkTreeReplaceNode(Schema):
    """Node shape for whole-tree PUT."""
    title = fields.Str(required=True)
    description = fields.Str(load_default="")
    is_leaf = fields.Bool(load_default=False)
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    assignees = fields.List(fields.Int(), load_default=[])
    children = fields.List(fields.Nested(lambda: BulkTreeReplaceNode), load_default=[])


class BulkTreeReplaceRequest(Schema):
    expected_version = fields.Int(allow_none=True, load_default=None)
    nodes = fields.List(fields.Nested(BulkTreeReplaceNode), required=True)


class NudgeRequest(Schema):
    message = fields.Str(load_default="")
