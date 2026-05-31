"""Helpers for JSON column / Redis serialization."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal


def json_safe(value):
    """Coerce values for JSON storage (dates, datetimes, decimals, nested structures)."""
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value
