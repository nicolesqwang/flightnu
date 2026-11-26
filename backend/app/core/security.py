import hmac

from fastapi import Header, HTTPException

from app.core.config import get_settings


def _matches(expected: str, given: str | None) -> bool:
    return given is not None and hmac.compare_digest(expected.encode(), given.encode())


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Guards destructive endpoints. Open when ADMIN_KEY is unset (local dev)."""
    key = get_settings().admin_key
    if key and not _matches(key, x_admin_key):
        raise HTTPException(status_code=401, detail="Admin key required for this action.")


def require_cron(x_cron_secret: str | None = Header(default=None)) -> None:
    secret = get_settings().cron_secret
    if not secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET is not configured on the server.")
    if not _matches(secret, x_cron_secret):
        raise HTTPException(status_code=401, detail="Invalid cron secret.")
