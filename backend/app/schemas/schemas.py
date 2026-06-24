from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import Recommendation, TrackingFrequency


class TrackerCreate(BaseModel):
    origin_airport: str = Field(min_length=3, max_length=3)
    destination_airport: str = Field(min_length=3, max_length=3)
    departure_date: date
    return_date: date | None = None
    tracking_frequency: TrackingFrequency = TrackingFrequency.EVERY_4_HOURS
    alerts_enabled: bool = True
    discord_webhook_url: str | None = None
    alert_email: EmailStr | None = None


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
    created_at: datetime


class PriceObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    price: float
    airline: str
    timestamp: datetime


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
    generated_at: datetime


class TrackerCardOut(BaseModel):
    tracker: TrackerOut
    current_price: float | None
    historical_average: float | None
    savings_opportunity: float | None
    confidence_score: float | None
    recommendation: Recommendation | None
    observation_count: int


class TrackerDetailOut(BaseModel):
    tracker: TrackerOut
    observations: list[PriceObservationOut]
    latest_prediction: PredictionOut | None
    prediction_history: list[PredictionOut]


class DashboardSummaryOut(BaseModel):
    total_active_trackers: int
    total_observations: int
    average_savings_opportunity: float
    average_prediction_confidence: float
    tracker_cards: list[TrackerCardOut]
