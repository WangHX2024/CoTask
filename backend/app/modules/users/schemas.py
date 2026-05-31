from marshmallow import Schema, fields, validate

from ...common.schemas import UTCDateTime


class UserProfile(Schema):
    id = fields.Int()
    name = fields.Str()
    phone = fields.Str()
    student_id = fields.Str()
    email = fields.Str()
    major = fields.Str()
    grade = fields.Str()
    avatar_url = fields.Str()
    bio = fields.Str()
    contribution = fields.Int()
    skills = fields.Method("get_skills")
    prefs = fields.Raw()
    created_at = UTCDateTime()

    def get_skills(self, obj):
        return [s.skill for s in (obj.skills or [])]


class UserUpdate(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=64))
    bio = fields.Str(validate=validate.Length(max=256))
    avatar_url = fields.Str(validate=validate.Length(max=256))
    major = fields.Str(validate=validate.Length(max=64))
    grade = fields.Str(validate=validate.Length(max=16))
    email = fields.Email()
    prefs = fields.Dict()


class SkillsUpdate(Schema):
    skills = fields.List(fields.Str(validate=validate.Length(min=1, max=32)), required=True)


class PasswordChange(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6, max=64))


class ContributionItem(Schema):
    id = fields.Int()
    delta = fields.Int()
    reason = fields.Str()
    ref_type = fields.Str()
    ref_id = fields.Int()
    created_at = UTCDateTime()


class ContributionSummary(Schema):
    total = fields.Int()
    level = fields.Int()
    title = fields.Str()
    items = fields.List(fields.Nested(ContributionItem))
