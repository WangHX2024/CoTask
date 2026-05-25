"""Unified error handling."""
from __future__ import annotations

import logging
import traceback

from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError

log = logging.getLogger(__name__)


class AppError(Exception):
    """Domain error with a stable code and HTTP status."""

    def __init__(self, code: str, message: str, http_status: int = 400, detail: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.detail = detail or {}

    def to_dict(self):
        return {"code": self.code, "message": self.message, "detail": self.detail}


# Common pre-baked errors
class NotFound(AppError):
    def __init__(self, what: str = "resource"):
        super().__init__("NOT_FOUND", f"{what} not found", 404)


class Forbidden(AppError):
    def __init__(self, msg: str = "forbidden"):
        super().__init__("FORBIDDEN", msg, 403)


class Unauthorized(AppError):
    def __init__(self, msg: str = "unauthorized"):
        super().__init__("UNAUTHORIZED", msg, 401)


class Conflict(AppError):
    def __init__(self, code: str, msg: str, detail: dict | None = None):
        super().__init__(code, msg, 409, detail)


class BadRequest(AppError):
    def __init__(self, code: str, msg: str, detail: dict | None = None):
        super().__init__(code, msg, 400, detail)


def register_error_handlers(app: Flask):
    @app.errorhandler(AppError)
    def handle_app_error(e: AppError):
        return jsonify(e.to_dict()), e.http_status

    @app.errorhandler(IntegrityError)
    def handle_integrity(e: IntegrityError):
        log.warning("IntegrityError: %s", e)
        return jsonify({"code": "INTEGRITY_ERROR", "message": "数据约束冲突"}), 409

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"code": "NOT_FOUND", "message": "资源不存在"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"code": "METHOD_NOT_ALLOWED", "message": "方法不允许"}), 405

    @app.errorhandler(422)
    def handle_422(e):
        # flask-smorest validation errors come through here
        data = getattr(e, "data", {})
        return jsonify({
            "code": "VALIDATION_ERROR",
            "message": "请求参数校验失败",
            "detail": data.get("errors", data),
        }), 422

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        log.error("Unhandled: %s\n%s", e, traceback.format_exc())
        return jsonify({"code": "INTERNAL_ERROR", "message": "服务内部错误"}), 500
