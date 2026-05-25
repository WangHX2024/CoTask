"""Shared marshmallow schemas."""
from marshmallow import Schema, fields


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
