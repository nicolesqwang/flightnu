from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PlainSerializer, field_validator, model_validator

from app.core.timeutil import utctoday
from app.models.models import Recommendation, TrackingFrequency
from app.services.airports import get_airport
from app.services.alerts import is_valid_discord_webhook

MAX_DAYS_AHEAD = 330  # airlines publish schedules ~11 months out


def _iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# Stored as naive UTC; always sent with a trailing "Z" so browsers convert
# to the viewer's local time correctly.
UTCDateTime = Annotated[datetime, PlainSerializer(_iso_utc, return_type=str)]


class TrackerCreate(BaseModel):
    origin_airport: str = Field(min_length=3, max_length=3)
    destination_airport: str = Field(min_length=3, max_length=3)
    departure_date: date
    return_date: date | None = None
    tracking_frequency: TrackingFrequency = TrackingFrequency.EVERY_4_HOURS
    alerts_enabled: bool = True
    discord_webhook_url: str | None = None
    alert_email: EmailStr | None = None

    @field_validator("origin_airport", "destination_airport")
    @classmethod
    def _airport(cls, v: str) -> str:
        code = v.strip().upper()
        if not code.isalpha() or get_airport(code) is None:
            raise ValueError(f"'{code}' is not a recognized airport code with scheduled flights.")
        return code

    @field_validator("discord_webhook_url")
    @classmethod
    def _webhook(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        if not is_valid_discord_webhook(v):
            raise ValueError("Discord webhook must look like https://discord.com/api/webhooks/<id>/<token>.")
        return v.strip()

    @model_validator(mode="after")
    def _dates_and_route(self):
        if self.origin_airport == self.destination_airport:
            raise ValueError("Origin and destination must be different airports.")
        today = utctoday()
        if self.departure_date < today:
            raise ValueError("Departure date is in the past.")
        if self.departure_date > today + timedelta(days=MAX_DAYS_AHEAD):
            raise ValueError(f"Departure date must be within {MAX_DAYS_AHEAD} days.")
        if self.return_date and self.return_date < self.departure_date:
            raise ValueError("Return date must be on or after the departure date.")
        return self


class TrackerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    origin_airport: str
    destination_airport: str
    departure_date: date
    return_date: date | None
    tracking_frequency: TrackingFrequency
    alerts_enabled: bool
    active: bool
    created_at: UTCDateTime
    last_checked_at: UTCDateTime | None = None
    last_error: str | None = None


class PriceObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    price: float
    airline: str
    timestamp: UTCDateTime
    source: str | None = None
    flight_number: str | None = None
    transfers: int | None = None
    booking_link: str | None = None


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    historical_average: float
    historical_low: float
    historical_high: float
    std_dev: float
    z_score: float
    current_price: float
    sma: float
    ewma: float
    predicted_price_24h: float
    predicted_price_48h: float
    prob_increase_24h: float
    prob_increase_48h: float
    expected_increase: float
    expected_decrease: float
    confidence_interval_low: float
    confidence_interval_high: float
    confidence_score: float
    recommendation: Recommendation
    explanation: str
    cheapest_day_of_week: str | None
    most_expensive_day_of_week: str | None
    cheapest_hour_of_day: int | None
    most_expensive_hour_of_day: int | None
    observation_count: int | None = None
    percentile: float | None = None
    days_to_departure: int | None = None
    has_forecast: bool | None = None
    generated_at: UTCDateTime


class TrackerCardOut(BaseModel):
    tracker: TrackerOut
    current_price: float | None
    historical_average: float | None
    savings_opportunity: float | None
    confidence_score: float | None
    recommendation: Recommendation | None
    observation_count: int
    data_source: str | None


class TrackerDetailOut(BaseModel):
    tracker: TrackerOut
    observations: list[PriceObservationOut]
    latest_prediction: PredictionOut | None
    prediction_history: list[PredictionOut]
    total_observations: int


class DashboardSummaryOut(BaseModel):
    total_active_trackers: int
    total_observations: int
    average_savings_opportunity: float
    average_prediction_confidence: float
    tracker_cards: list[TrackerCardOut]


class ServerStatusOut(BaseModel):
    price_provider: str
    provider_configured: bool
    serpapi_configured: bool
    admin_key_required: bool
    max_active_trackers: int
    active_trackers: int
    last_ingest_at: UTCDateTime | None


class AirportOut(BaseModel):
    code: str
    name: str
    city: str
    country: str


class IngestOut(BaseModel):
    checked: int
    fetched: int
    skipped_not_due: int
    deactivated: int
    errors: list[str]
