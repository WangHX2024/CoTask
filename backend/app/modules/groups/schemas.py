from marshmallow import Schema, fields, validate


class GroupCreate(Schema):
    course_name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=512))


class GroupUpdate(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=128))
    course_name = fields.Str(validate=validate.Length(min=1, max=128))
    description = fields.Str(validate=validate.Length(max=512))


class GroupBrief(Schema):
    id = fields.Int()
    course_name = fields.Str()
    name = fields.Str()
    invite_code = fields.Str()
    status = fields.Str()
    description = fields.Str()
    created_by = fields.Int()
    created_at = fields.DateTime()
    role = fields.Str()
    member_count = fields.Int()
    progress = fields.Int()


class JoinRequest(Schema):
    invite_code = fields.Str(required=True, validate=validate.Length(equal=8))


class MemberInfo(Schema):
    user_id = fields.Int()
    name = fields.Str()
    avatar_url = fields.Str()
    role = fields.Str()
    anon_id = fields.Str()
    joined_at = fields.DateTime()
    contribution = fields.Int()
    skills = fields.List(fields.Str())


class TransferRequest(Schema):
    target_user_id = fields.Int(required=True)


class DissolveRequest(Schema):
    confirm_name = fields.Str(required=True)
