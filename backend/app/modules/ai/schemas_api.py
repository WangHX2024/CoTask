"""Marshmallow API schemas for AI endpoints."""
from marshmallow import INCLUDE, Schema, fields, validate

from ...common.schemas import UTCDateTime


class JobCreate(Schema):
    class Meta:
        unknown = INCLUDE

    scope = fields.Str(required=True, validate=validate.OneOf([
        "tree_gen", "tree_edit", "daily_advice", "assignment"
    ]))
    group_id = fields.Int(allow_none=True)
    payload = fields.Dict(load_default=dict)
    conversation_id = fields.Int(allow_none=True, load_default=None, required=False)


class AiMessageInfo(Schema):
    role = fields.Str()
    content = fields.Str()
    created_at = UTCDateTime()


class JobInfo(Schema):
    id = fields.Int()
    scope = fields.Str()
    status = fields.Str()
    result = fields.Raw()
    error = fields.Str(allow_none=True)
    created_at = UTCDateTime()
