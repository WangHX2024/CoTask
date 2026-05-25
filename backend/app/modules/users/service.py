from __future__ import annotations

import bcrypt

from ...common.errors import BadRequest, NotFound
from ...common.tx import tx
from ...extensions import db
from ...models import ContributionLog, User, UserSkill


def get_user(uid: int) -> User:
    u = db.session.get(User, uid)
    if not u or u.deleted_at is not None:
        raise NotFound("user")
    return u


def update_profile(uid: int, data: dict) -> User:
    user = get_user(uid)
    with tx():
        for k, v in data.items():
            if hasattr(user, k) and v is not None:
                setattr(user, k, v)
    return user


def set_skills(uid: int, skills: list[str]) -> list[str]:
    user = get_user(uid)
    skills_clean = [s.strip()[:32] for s in dict.fromkeys(skills) if s.strip()][:30]
    with tx() as s:
        s.execute(db.delete(UserSkill).where(UserSkill.user_id == user.id))
        for skill in skills_clean:
            s.add(UserSkill(user_id=user.id, skill=skill))
    return skills_clean


def change_password(uid: int, current: str, new: str):
    user = get_user(uid)
    if not user.password_hash or not bcrypt.checkpw(current.encode(), user.password_hash.encode()):
        raise BadRequest("BAD_PASSWORD", "当前密码错误")
    with tx():
        user.password_hash = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()


def adjust_contribution(uid: int, delta: int, reason: str, ref_type: str | None = None,
                       ref_id: int | None = None):
    """Adjust a user's contribution score; called from other services."""
    user = get_user(uid)
    user.contribution = (user.contribution or 0) + delta
    db.session.add(
        ContributionLog(
            user_id=uid, delta=delta, reason=reason, ref_type=ref_type, ref_id=ref_id
        )
    )


def contribution_summary(uid: int, limit: int = 30):
    user = get_user(uid)
    items = (
        db.session.execute(
            db.select(ContributionLog)
            .where(ContributionLog.user_id == uid)
            .order_by(ContributionLog.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    total = user.contribution
    level = _level_for(total)
    return {
        "total": total,
        "level": level,
        "title": _level_title(level),
        "items": items,
    }


def _level_for(score: int) -> int:
    thresholds = [0, 50, 150, 350, 700, 1200, 2000]
    for i, t in enumerate(thresholds):
        if score < t:
            return max(0, i - 1)
    return len(thresholds) - 1


def _level_title(level: int) -> str:
    titles = ["新苗", "见习生", "协作能手", "项目能人", "高效团队人", "课程领袖", "传奇组长"]
    return titles[min(level, len(titles) - 1)]
