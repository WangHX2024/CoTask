from __future__ import annotations

import logging

import bcrypt
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from ...common.errors import BadRequest, Conflict, Unauthorized
from ...common.sms_service import AliyunSmsService, aliyun_sms_configured
from ...common.tx import tx
from ...common.utils import gen_sms_code, is_valid_phone
from ...extensions import db, get_redis
from ...models import User

log = logging.getLogger(__name__)


def _hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _check_pw(pw: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def _use_aliyun_sms() -> bool:
    provider = current_app.config.get("SMS_PROVIDER", "stub")
    if provider != "aliyun":
        return False
    if not aliyun_sms_configured():
        raise BadRequest("SMS_NOT_CONFIGURED", "短信服务未配置，请联系管理员")
    return True


def send_sms(phone: str, purpose: str = "register") -> None:
    if not is_valid_phone(phone):
        raise BadRequest("INVALID_PHONE", "手机号格式不正确")

    r = get_redis()
    rate_key = f"sms:rate:{phone}"
    if r.get(rate_key):
        raise BadRequest("SMS_RATE_LIMIT", "请稍后再试")
    r.setex(rate_key, 60, "1")

    if _use_aliyun_sms():
        if not AliyunSmsService.send_verification_code(phone):
            raise BadRequest("SMS_SEND_FAILED", "验证码发送失败，请稍后重试")
        return

    code = gen_sms_code(current_app.config["SMS_CODE_LENGTH"])
    r.setex(f"sms:{purpose}:{phone}", current_app.config["SMS_CODE_TTL"], code)
    log.warning("[SMS-STUB] %s purpose=%s code=%s", phone, purpose, code)


def _verify_code(phone: str, code: str, purpose: str):
    if _use_aliyun_sms():
        if not AliyunSmsService.verify_code(phone, code):
            raise BadRequest("INVALID_CODE", "验证码错误或已过期")
        return

    r = get_redis()
    key = f"sms:{purpose}:{phone}"
    saved = r.get(key)
    if not saved or saved != code:
        raise BadRequest("INVALID_CODE", "验证码错误或已过期")
    r.delete(key)


def register(data: dict) -> tuple[User, str, str]:
    phone = data["phone"]
    _verify_code(phone, data["code"], "register")

    existing = db.session.execute(
        db.select(User).where(User.phone == phone)
    ).scalar_one_or_none()
    if existing:
        raise Conflict("PHONE_EXISTS", "该手机号已注册")

    if data.get("student_id"):
        dup = db.session.execute(
            db.select(User).where(User.student_id == data["student_id"])
        ).scalar_one_or_none()
        if dup:
            raise Conflict("STUDENT_ID_EXISTS", "该学号已被使用")

    with tx() as s:
        user = User(
            phone=phone,
            name=data["name"],
            password_hash=_hash_pw(data["password"]),
            student_id=data.get("student_id"),
            major=data.get("major"),
            prefs={"theme": "auto", "notify": {"email": True, "inapp": True}},
        )
        s.add(user)
        s.flush()
    access, refresh = create_access_token(identity=str(user.id)), create_refresh_token(identity=str(user.id))
    return user, access, refresh


def login(account: str, password: str) -> tuple[User, str, str]:
    r = get_redis()
    fail_key = f"login:fail:{account}"
    fails = int(r.get(fail_key) or "0")
    if fails >= 10:
        raise Unauthorized("失败次数过多，请稍后再试")

    if is_valid_phone(account):
        user = db.session.execute(db.select(User).where(User.phone == account)).scalar_one_or_none()
    else:
        user = db.session.execute(db.select(User).where(User.student_id == account)).scalar_one_or_none()

    if not user or not _check_pw(password, user.password_hash) or user.deleted_at is not None:
        r.setex(fail_key, 300, fails + 1)
        raise Unauthorized("账号或密码错误")

    r.delete(fail_key)
    return user, create_access_token(identity=str(user.id)), create_refresh_token(identity=str(user.id))


def reset_password(phone: str, code: str, new_password: str):
    _verify_code(phone, code, "reset")
    user = db.session.execute(db.select(User).where(User.phone == phone)).scalar_one_or_none()
    if not user:
        raise BadRequest("USER_NOT_FOUND", "用户不存在")
    with tx():
        user.password_hash = _hash_pw(new_password)
