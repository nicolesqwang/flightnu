from datetime import date, datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (how it is stored in the DB)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utctoday() -> date:
    return datetime.now(timezone.utc).date()


def to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)
