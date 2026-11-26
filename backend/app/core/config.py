from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./flightnu.db"
    environment: str = "development"

    # --- Price data -------------------------------------------------------
    # "travelpayouts" (default, free, real cached fares from Aviasales searches),
    # "serpapi" (Google Flights via SerpApi, 250 free searches/month), or
    # "simulator" (synthetic demo data; every observation is labelled as such).
    price_provider: str = "travelpayouts"
    travelpayouts_token: str | None = None
    travelpayouts_market: str = "us"
    serpapi_key: str | None = None
    # When the primary provider has no fare cached for a route, try SerpApi
    # (if a key is set). Also used once per new tracker to backfill real
    # price history from Google Flights' price_insights.
    serpapi_fallback: bool = True
    serpapi_backfill_on_create: bool = True
    currency: str = "usd"

    # --- Scheduling -------------------------------------------------------
    # Seconds between manual "Refresh Now" fetches for one tracker.
    refresh_cooldown_seconds: int = 600
    # Secret that the scheduled GitHub Action sends to /api/internal/ingest.
    cron_secret: str | None = None

    # --- Access control ---------------------------------------------------
    # When set, deleting / pausing trackers requires header X-Admin-Key.
    admin_key: str | None = None
    # Cap on active trackers so public visitors can't exhaust API quotas.
    max_active_trackers: int = 12
    # Create demo trackers automatically when the database is empty.
    auto_seed: bool = True

    # --- Alerts -----------------------------------------------------------
    discord_webhook_url: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    alert_from_email: str | None = None

    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        # Neon / Heroku style URLs use "postgres://", which SQLAlchemy 2 rejects.
        if v.startswith("postgres://"):
            return "postgresql://" + v[len("postgres://"):]
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
