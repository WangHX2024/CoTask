"""Permission helpers — group-scoped role checks."""
from __future__ import annotations

from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db, get_redis
from .errors import Forbidden, Unauthorized


def current_user_id() -> int:
    try:
        verify_jwt_in_request()
    except Exception as e:
        raise Unauthorized(str(e)) from e
    ident = get_jwt_identity()
    if ident is None:
        raise Unauthorized()
    return int(ident)


def get_group_role(user_id: int, group_id: int) -> str | None:
    """Return 'leader' / 'member' / None. Cached in Redis for 60s."""
    cache_key = f"role:{user_id}:{group_id}"
    r = get_redis()
    cached = r.get(cache_key)
    if cached:
        return None if cached == "__none__" else cached

    from ..models import GroupMember

    row = db.session.execute(
        db.select(GroupMember).where(
            GroupMember.user_id == user_id, GroupMember.group_id == group_id
        )
    ).scalar_one_or_none()

    role = row.role if row else None
    r.setex(cache_key, 60, role or "__none__")
    return role


def invalidate_role_cache(user_id: int, group_id: int):
    get_redis().delete(f"role:{user_id}:{group_id}")


def require_group_role(required: str = "member"):
    """Decorator: ensure caller is a member (or leader) of path's `group_id`.

    `required='leader'` forces leader-only.
    `required='member'` accepts both roles.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            uid = current_user_id()
            gid = kwargs.get("group_id") or kwargs.get("gid")
            if gid is None:
                raise Forbidden("missing group_id in path")
            role = get_group_role(uid, int(gid))
            if role is None:
                raise Forbidden("不是该小组成员")
            if required == "leader" and role != "leader":
                raise Forbidden("仅组长可执行")
            g.current_user_id = uid
            g.current_group_id = int(gid)
            g.current_role = role
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        g.current_user_id = current_user_id()
        return fn(*args, **kwargs)

    return wrapper
