"""Utilidades de tiempo compartidas entre servicios."""
from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
