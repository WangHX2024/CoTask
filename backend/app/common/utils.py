"""Misc helpers."""
import random
import re
import secrets
import string


def gen_invite_code(length: int = 8) -> str:
    """8-char invite, ambiguous chars removed."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def gen_anon_id(length: int = 4) -> str:
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def gen_sms_code(length: int = 4) -> str:
    return "".join(random.choice(string.digits) for _ in range(length))


PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


def is_valid_phone(s: str) -> bool:
    return bool(PHONE_RE.match(s or ""))


def slugify(s: str) -> str:
    s = re.sub(r"[^\w一-鿿]+", "-", s.strip())
    return s.strip("-").lower()
