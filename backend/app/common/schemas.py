"""Shared marshmallow schemas."""
from datetime import date, datetime

from marshmallow import Schema, fields

from .datetime_util import to_api_datetime


class UTCDateTime(fields.DateTime):
    """Serialize DB naive UTC datetimes as ISO-8601 with Z suffix."""

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, (datetime, date)):
            return to_api_datetime(value)
        return super()._serialize(value, attr, obj, **kwargs)


class PaginationMeta(Schema):
    page = fields.Int()
    size = fields.Int()
    total = fields.Int()
    pages = fields.Int()


class PaginationQuery(Schema):
    page = fields.Int(load_default=1)
    size = fields.Int(load_default=20)


class OkResponse(Schema):
    ok = fields.Bool(dump_default=True)


def paginated_response(item_schema_cls):
    class _PaginatedResponse(Schema):
        items = fields.List(fields.Nested(item_schema_cls))
        meta = fields.Nested(PaginationMeta)

    _PaginatedResponse.__name__ = f"Paginated{item_schema_cls.__name__}"
    return _PaginatedResponse
