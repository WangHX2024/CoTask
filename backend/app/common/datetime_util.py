"""UTC storage and ISO-8601 API serialization for datetimes."""
from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

# Product calendar day (DDL, dashboard "today") — align with Celery timezone.
APP_TIMEZONE = ZoneInfo("Asia/Shanghai")


def app_today() -> date:
    """Calendar date in APP_TIMEZONE (not server UTC)."""
    return datetime.now(APP_TIMEZONE).date()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def assume_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_api_datetime(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    return assume_utc(value).isoformat().replace("+00:00", "Z")
