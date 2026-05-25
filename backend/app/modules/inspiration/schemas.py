from marshmallow import Schema, fields, validate

CATEGORIES = ["template", "case", "tip", "script", "tool", "link"]
SORTS = ["latest", "hot", "favorites"]


class PostQuery(Schema):
    category = fields.Str(validate=validate.OneOf(CATEGORIES))
    course = fields.Str()
    sort = fields.Str(load_default="latest", validate=validate.OneOf(SORTS))
    q = fields.Str()
    page = fields.Int(load_default=1)
    size = fields.Int(load_default=20)
    mine = fields.Bool(load_default=False)
    favorites = fields.Bool(load_default=False)


class PostBrief(Schema):
    id = fields.Int()
    title = fields.Str()
    cover_url = fields.Str()
    category = fields.Str()
    course_tag = fields.Str()
    author_id = fields.Int()
    author_name = fields.Str()
    author_avatar = fields.Str()
    anon = fields.Bool()
    likes = fields.Int()
    favs = fields.Int()
    comments = fields.Int()
    link_url = fields.Str()
    has_template = fields.Bool()
    excerpt = fields.Str()
    created_at = fields.DateTime()
    liked_by_me = fields.Bool()
    favored_by_me = fields.Bool()


class PostDetail(PostBrief):
    body_md = fields.Str()
    template_root_id = fields.Int(allow_none=True)


class PostCreate(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    category = fields.Str(required=True, validate=validate.OneOf(CATEGORIES))
    body_md = fields.Str(load_default="")
    cover_url = fields.Str()
    course_tag = fields.Str()
    link_url = fields.Str()
    anon = fields.Bool(load_default=False)
    template_from_group_id = fields.Int(allow_none=True)


class PostUpdate(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=256))
    body_md = fields.Str()
    cover_url = fields.Str()
    course_tag = fields.Str()
    link_url = fields.Str()


class CommentCreate(Schema):
    body = fields.Str(required=True, validate=validate.Length(min=1, max=2000))
    parent_id = fields.Int(allow_none=True, load_default=None)
    anon = fields.Bool(load_default=False)


class CommentBrief(Schema):
    id = fields.Int()
    post_id = fields.Int()
    body = fields.Str()
    author_id = fields.Int()
    author_name = fields.Str()
    author_avatar = fields.Str()
    anon = fields.Bool()
    parent_id = fields.Int(allow_none=True)
    created_at = fields.DateTime()


class TemplateImportRequest(Schema):
    to_group_id = fields.Int(required=True)
    mode = fields.Str(load_default="replace", validate=validate.OneOf(["replace", "append"]))


class ListResponse(Schema):
    items = fields.List(fields.Nested(PostBrief))
    total = fields.Int()
    page = fields.Int()
    size = fields.Int()
