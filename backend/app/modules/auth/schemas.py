from marshmallow import Schema, fields, validate


class SmsRequest(Schema):
    phone = fields.Str(required=True, validate=validate.Regexp(r"^1[3-9]\d{9}$"))
    purpose = fields.Str(load_default="register", validate=validate.OneOf(["register", "reset"]))


class RegisterRequest(Schema):
    phone = fields.Str(required=True, validate=validate.Regexp(r"^1[3-9]\d{9}$"))
    code = fields.Str(required=True, validate=validate.Length(min=4, max=8))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=64))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    student_id = fields.Str(load_default=None, validate=validate.Length(max=32))
    major = fields.Str(load_default=None, validate=validate.Length(max=64))


class LoginRequest(Schema):
    account = fields.Str(required=True)  # phone or student_id
    password = fields.Str(required=True)


class ResetPasswordRequest(Schema):
    phone = fields.Str(required=True, validate=validate.Regexp(r"^1[3-9]\d{9}$"))
    code = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6, max=64))


class UserBrief(Schema):
    id = fields.Int()
    name = fields.Str()
    phone = fields.Str()
    student_id = fields.Str()
    avatar_url = fields.Str()
    major = fields.Str()
    grade = fields.Str()
    bio = fields.Str()
    contribution = fields.Int()


class AuthResponse(Schema):
    access_token = fields.Str()
    refresh_token = fields.Str()
    user = fields.Nested(UserBrief)


class OkSchema(Schema):
    ok = fields.Bool(dump_default=True)
    message = fields.Str(dump_default="")
