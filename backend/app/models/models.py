import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Recommendation(str, enum.Enum):
    BUY_NOW = "BUY_NOW"
    WAIT = "WAIT"
    MONITOR = "MONITOR"


class TrackingFrequency(str, enum.Enum):
    HOURLY = "HOURLY"
    EVERY_4_HOURS = "EVERY_4_HOURS"
    DAILY = "DAILY"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trackers: Mapped[list["Tracker"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Tracker(Base):
    __tablename__ = "trackers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    origin_airport: Mapped[str] = mapped_column(String(3))
    destination_airport: Mapped[str] = mapped_column(String(3))
    departure_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tracking_frequency: Mapped[TrackingFrequency] = mapped_column(
        Enum(TrackingFrequency), default=TrackingFrequency.EVERY_4_HOURS
    )
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    discord_webhook_url: Mapped[str | None] = mapped_column(String, nullable=True)
    alert_email: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="trackers")
    observations: Mapped[list["PriceObservation"]] = relationship(
        back_populates="tracker", cascade="all, delete-orphan", order_by="PriceObservation.timestamp"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="tracker", cascade="all, delete-orphan", order_by="Prediction.generated_at"
    )


class PriceObservation(Base):
    __tablename__ = "price_observations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    tracker_id: Mapped[str] = mapped_column(String, ForeignKey("trackers.id"), index=True)
    price: Mapped[float] = mapped_column(Float)
    airline: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    tracker: Mapped["Tracker"] = relationship(back_populates="observations")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    tracker_id: Mapped[str] = mapped_column(String, ForeignKey("trackers.id"), index=True)

    historical_average: Mapped[float] = mapped_column(Float)
    historical_low: Mapped[float] = mapped_column(Float)
    historical_high: Mapped[float] = mapped_column(Float)
    std_dev: Mapped[float] = mapped_column(Float, default=0.0)
    z_score: Mapped[float] = mapped_column(Float)

    current_price: Mapped[float] = mapped_column(Float)
    sma: Mapped[float] = mapped_column(Float, default=0.0)
    ewma: Mapped[float] = mapped_column(Float, default=0.0)

    predicted_price_24h: Mapped[float] = mapped_column(Float)
    predicted_price_48h: Mapped[float] = mapped_column(Float)
    prob_increase_24h: Mapped[float] = mapped_column(Float, default=0.0)
    prob_increase_48h: Mapped[float] = mapped_column(Float, default=0.0)
    expected_increase: Mapped[float] = mapped_column(Float, default=0.0)
    expected_decrease: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_interval_low: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_interval_high: Mapped[float] = mapped_column(Float, default=0.0)

    confidence_score: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[Recommendation] = mapped_column(Enum(Recommendation))
    explanation: Mapped[str] = mapped_column(String, default="")

    cheapest_day_of_week: Mapped[str | None] = mapped_column(String, nullable=True)
    most_expensive_day_of_week: Mapped[str | None] = mapped_column(String, nullable=True)
    cheapest_hour_of_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    most_expensive_hour_of_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    tracker: Mapped["Tracker"] = relationship(back_populates="predictions")
