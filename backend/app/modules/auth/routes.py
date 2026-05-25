from flask import jsonify, make_response
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from flask_smorest import Blueprint

from .schemas import (
    AuthResponse,
    LoginRequest,
    OkSchema,
    RegisterRequest,
    ResetPasswordRequest,
    SmsRequest,
    UserBrief,
)
from .service import login as svc_login
from .service import register as svc_register
from .service import reset_password as svc_reset
from .service import send_sms as svc_sms

blp = Blueprint("auth", "auth", url_prefix="/api/auth", description="账号认证")


def _auth_resp(user, access, refresh):
    body = {"access_token": access, "refresh_token": refresh, "user": _user_brief(user)}
    resp = make_response(jsonify(body))
    set_refresh_cookies(resp, refresh)
    return resp


def _user_brief(u):
    return {
        "id": u.id,
        "name": u.name,
        "phone": u.phone,
        "student_id": u.student_id,
        "avatar_url": u.avatar_url,
        "major": u.major,
        "grade": u.grade,
        "bio": u.bio,
        "contribution": u.contribution,
    }


@blp.route("/sms")
class Sms(MethodView):
    @blp.arguments(SmsRequest)
    @blp.response(200, OkSchema)
    def post(self, data):
        svc_sms(data["phone"], data["purpose"])
        return {"ok": True, "message": "验证码已发送"}


@blp.route("/register")
class Register(MethodView):
    @blp.arguments(RegisterRequest)
    def post(self, data):
        user, access, refresh = svc_register(data)
        return _auth_resp(user, access, refresh), 201


@blp.route("/login")
class Login(MethodView):
    @blp.arguments(LoginRequest)
    def post(self, data):
        user, access, refresh = svc_login(data["account"], data["password"])
        return _auth_resp(user, access, refresh)


@blp.route("/refresh")
class Refresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        uid = get_jwt_identity()
        access = create_access_token(identity=uid)
        return jsonify({"access_token": access, "refresh_token": "", "user": None})


@blp.route("/logout")
class Logout(MethodView):
    def post(self):
        resp = make_response(jsonify({"ok": True}))
        unset_jwt_cookies(resp)
        return resp


@blp.route("/reset-password")
class Reset(MethodView):
    @blp.arguments(ResetPasswordRequest)
    @blp.response(200, OkSchema)
    def post(self, data):
        svc_reset(data["phone"], data["code"], data["new_password"])
        return {"ok": True, "message": "密码已重置"}


@blp.route("/me")
class Me(MethodView):
    @jwt_required()
    @blp.response(200, UserBrief)
    def get(self):
        from ...extensions import db
        from ...models import User

        uid = int(get_jwt_identity())
        user = db.session.get(User, uid)
        return user
