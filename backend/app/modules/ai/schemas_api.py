"""Marshmallow API schemas for AI endpoints."""
from marshmallow import Schema, fields, validate


class JobCreate(Schema):
    scope = fields.Str(required=True, validate=validate.OneOf([
        "tree_gen", "tree_edit", "daily_advice", "assignment"
    ]))
    group_id = fields.Int(allow_none=True)
    payload = fields.Dict(load_default=dict)


class JobInfo(Schema):
    id = fields.Int()
    scope = fields.Str()
    status = fields.Str()
    result = fields.Raw()
    error = fields.Str(allow_none=True)
    created_at = fields.DateTime()
