"""Aliyun SMS authentication service (PNVS / dypnsapi).

Docs: https://help.aliyun.com/zh/pnvs/user-guide/sms-authentication-service
"""
from __future__ import annotations

import json
import logging

from flask import current_app

log = logging.getLogger(__name__)


def _cfg(name: str, default: str | int | None = None):
    return current_app.config.get(name, default)


def aliyun_sms_configured() -> bool:
    return bool(_cfg("SMS_ACCESS_KEY") and _cfg("SMS_SECRET_KEY"))


class AliyunSmsService:
    """Send and verify codes via Aliyun; codes are generated and checked by Aliyun."""

    @classmethod
    def send_verification_code(cls, phone: str) -> bool:
        if not aliyun_sms_configured():
            log.warning("Aliyun SMS keys missing; cannot send to %s", phone)
            return False
        return cls._send(phone)

    @classmethod
    def verify_code(cls, phone: str, code: str) -> bool:
        if not aliyun_sms_configured():
            log.warning("Aliyun SMS keys missing; cannot verify %s", phone)
            return False
        return cls._verify(phone, code)

    @classmethod
    def _client(cls):
        from alibabacloud_dypnsapi20170525.client import Client as DypnsapiClient
        from alibabacloud_tea_openapi import models as open_api_models

        config = open_api_models.Config(
            access_key_id=_cfg("SMS_ACCESS_KEY"),
            access_key_secret=_cfg("SMS_SECRET_KEY"),
            endpoint="dypnsapi.aliyuncs.com",
        )
        return DypnsapiClient(config)

    @classmethod
    def _send(cls, phone: str) -> bool:
        from alibabacloud_dypnsapi20170525 import models as dypnsapi_models

        try:
            ttl = int(_cfg("SMS_CODE_TTL", 300))
            client = cls._client()
            request = dypnsapi_models.SendSmsVerifyCodeRequest(
                phone_number=phone,
                sign_name=_cfg("SMS_AUTH_SIGN_NAME", "速通互联验证平台"),
                template_code=_cfg("SMS_AUTH_TEMPLATE_CODE", "100001"),
                template_param=json.dumps(
                    {"code": "##code##", "min": str(ttl // 60)},
                    ensure_ascii=False,
                ),
                country_code=str(_cfg("SMS_COUNTRY_CODE", "86")),
            )
            response = client.send_sms_verify_code(request)
            if response.body.code == "OK":
                log.info("SMS sent via Aliyun: %s", phone)
                return True
            log.error(
                "Aliyun SMS send failed: %s - %s",
                response.body.code,
                response.body.message,
            )
            return False
        except Exception as exc:
            log.exception("Aliyun SMS send error: %s", exc)
            return False

    @classmethod
    def _verify(cls, phone: str, code: str) -> bool:
        from alibabacloud_dypnsapi20170525 import models as dypnsapi_models

        try:
            client = cls._client()
            request = dypnsapi_models.CheckSmsVerifyCodeRequest(
                phone_number=phone,
                verify_code=code,
                country_code=str(_cfg("SMS_COUNTRY_CODE", "86")),
            )
            response = client.check_sms_verify_code(request)
            if response.body.code == "OK":
                log.info("SMS verified via Aliyun: %s", phone)
                return True
            log.warning(
                "Aliyun SMS verify failed: %s - %s",
                response.body.code,
                response.body.message,
            )
            return False
        except Exception as exc:
            log.exception("Aliyun SMS verify error: %s", exc)
            return False
