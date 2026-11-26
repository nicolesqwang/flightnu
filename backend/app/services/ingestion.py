"""Fetch real prices, store them, recompute analytics, send alerts."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timeutil import utcnow
from app.models.models import FREQUENCY_HOURS, PriceObservation, Prediction, Tracker
from app.services import alerts
from app.services.analytics import run_analytics
from app.services.pricing import fetch_current_price, fetch_history
from app.services.providers.base import PriceQuote

logger = logging.getLogger("flightnu.ingestion")

PREDICTIONS_KEPT_PER_TRACKER = 300
ALERT_COOLDOWN = timedelta(hours=24)
# A tracker counts as due slightly early so an hourly cron never skips a 4h slot.
DUE_SLACK = timedelta(minutes=10)


def _observations(db: Session, tracker_id: str) -> list[PriceObservation]:
    return list(
        db.scalars(
            select(PriceObservation)
            .where(PriceObservation.tracker_id == tracker_id)
            .order_by(PriceObservation.timestamp)
        )
    )


def last_observation(db: Session, tracker_id: str) -> PriceObservation | None:
    return db.scalars(
        select(PriceObservation)
        .where(PriceObservation.tracker_id == tracker_id)
        .order_by(PriceObservation.timestamp.desc())
        .limit(1)
    ).first()


def latest_prediction(db: Session, tracker_id: str) -> Prediction | None:
    return db.scalars(
        select(Prediction).where(Prediction.tracker_id == tracker_id).order_by(Prediction.generated_at.desc()).limit(1)
    ).first()


def record_quote(db: Session, tracker: Tracker, quote: PriceQuote, timestamp: datetime | None = None) -> PriceObservation:
    obs = PriceObservation(
        tracker_id=tracker.id,
        price=quote.price,
        airline=quote.airline,
        timestamp=timestamp or quote.observed_at or utcnow(),
        source=quote.source,
        flight_number=quote.flight_number,
        transfers=quote.transfers,
        booking_link=quote.booking_link,
    )
    db.add(obs)
    db.flush()
    return obs


def recompute(db: Session, tracker: Tracker, now: datetime | None = None, send_alerts: bool = True) -> Prediction | None:
    now = now or utcnow()
    result = run_analytics(_observations(db, tracker.id), tracker.departure_date, now)
    if result is None:
        return None

    prediction = Prediction(
        tracker_id=tracker.id,
        historical_average=result.historical_average,
        historical_low=result.historical_low,
        historical_high=result.historical_high,
        std_dev=result.std_dev,
        z_score=result.z_score,
        current_price=result.current_price,
        sma=result.sma,
        ewma=result.ewma,
        predicted_price_24h=result.predicted_price_24h,
        predicted_price_48h=result.predicted_price_48h,
        prob_increase_24h=result.prob_increase_24h,
        prob_increase_48h=result.prob_increase_48h,
        expected_increase=result.expected_increase,
        expected_decrease=result.expected_decrease,
        confidence_interval_low=result.confidence_interval_low,
        confidence_interval_high=result.confidence_interval_high,
        confidence_score=result.confidence_score,
        recommendation=result.recommendation,
        explanation=result.explanation,
        cheapest_day_of_week=result.cheapest_day_of_week,
        most_expensive_day_of_week=result.most_expensive_day_of_week,
        cheapest_hour_of_day=result.cheapest_hour_of_day,
        most_expensive_hour_of_day=result.most_expensive_hour_of_day,
        observation_count=result.observation_count,
        percentile=result.percentile,
        days_to_departure=result.days_to_departure,
        has_forecast=result.has_forecast,
        generated_at=now,
    )
    db.add(prediction)
    db.flush()
    _prune_predictions(db, tracker.id)
    db.commit()

    if send_alerts and prediction.recommendation.value == "BUY_NOW" and tracker.alerts_enabled:
        if tracker.last_alert_at is None or now - tracker.last_alert_at >= ALERT_COOLDOWN:
            try:
                if alerts.dispatch_alerts(tracker, prediction):
                    tracker.last_alert_at = now
                    db.commit()
            except Exception:
                logger.exception("Alert dispatch failed for tracker %s", tracker.id)
    return prediction


def _prune_predictions(db: Session, tracker_id: str) -> None:
    stale_ids = list(
        db.scalars(
            select(Prediction.id)
            .where(Prediction.tracker_id == tracker_id)
            .order_by(Prediction.generated_at.desc())
            .offset(PREDICTIONS_KEPT_PER_TRACKER)
        )
    )
    if stale_ids:
        db.query(Prediction).filter(Prediction.id.in_(stale_ids)).delete(synchronize_session=False)


@dataclass
class UpdateOutcome:
    prediction: Prediction | None
    fetched: bool
    error: str | None = None


def fetch_and_update(db: Session, tracker: Tracker, now: datetime | None = None) -> UpdateOutcome:
    """Fetch one real price; store it and recompute analytics if one was found."""
    now = now or utcnow()
    prev = last_observation(db, tracker.id)
    outcome = fetch_current_price(tracker, previous_price=prev.price if prev else None)
    tracker.last_checked_at = now
    tracker.last_error = outcome.error
    if outcome.quote is None:
        db.commit()
        return UpdateOutcome(latest_prediction(db, tracker.id), fetched=False, error=outcome.error)
    record_quote(db, tracker, outcome.quote, timestamp=now)
    db.commit()
    return UpdateOutcome(recompute(db, tracker, now), fetched=True)


def initialize_tracker(db: Session, tracker: Tracker) -> UpdateOutcome:
    """First fetch for a new tracker: backfill real price history when SerpApi
    is configured, then take a current reading."""
    now = utcnow()
    history = fetch_history(tracker)
    for point in history:
        if point.observed_at is not None:
            record_quote(db, tracker, point)
    db.commit()

    outcome = fetch_and_update(db, tracker, now)
    if not outcome.fetched:
        live = [p for p in history if p.observed_at is None]
        if live:
            record_quote(db, tracker, live[-1], timestamp=now)
            tracker.last_error = None
            db.commit()
            return UpdateOutcome(recompute(db, tracker, now), fetched=True)
        if history:
            return UpdateOutcome(recompute(db, tracker, now, send_alerts=False), fetched=False, error=outcome.error)
    return outcome


def is_due(db: Session, tracker: Tracker, now: datetime) -> bool:
    interval = timedelta(hours=FREQUENCY_HOURS[tracker.tracking_frequency])
    last = tracker.last_checked_at
    return last is None or now - last >= interval - DUE_SLACK


def deactivate_departed(db: Session, now: datetime) -> int:
    departed = db.scalars(
        select(Tracker).where(Tracker.active.is_(True), Tracker.departure_date < now.date())
    ).all()
    for t in departed:
        t.active = False
    db.commit()
    return len(departed)


@dataclass
class IngestSummary:
    checked: int = 0
    fetched: int = 0
    skipped_not_due: int = 0
    deactivated: int = 0
    errors: list[str] = field(default_factory=list)


def run_due_trackers(db: Session, force: bool = False) -> IngestSummary:
    now = utcnow()
    summary = IngestSummary(deactivated=deactivate_departed(db, now))
    trackers = db.scalars(select(Tracker).where(Tracker.active.is_(True))).all()
    for tracker in trackers:
        if not force and not is_due(db, tracker, now):
            summary.skipped_not_due += 1
            continue
        summary.checked += 1
        try:
            outcome = fetch_and_update(db, tracker, now)
            if outcome.fetched:
                summary.fetched += 1
            elif outcome.error:
                summary.errors.append(f"{tracker.origin_airport}-{tracker.destination_airport}: {outcome.error}")
        except Exception as exc:  # keep going for the other trackers
            logger.exception("Failed to process tracker %s", tracker.id)
            db.rollback()
            summary.errors.append(f"{tracker.origin_airport}-{tracker.destination_airport}: {exc}")
    return summary
