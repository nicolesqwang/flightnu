from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import PriceObservation, Prediction, Tracker
from app.services import alerts
from app.services.analytics import run_analytics
from app.services.simulator import simulate_price

logger = logging.getLogger("flightnu.ingestion")


def process_tracker(db: Session, tracker: Tracker) -> Prediction | None:
    """Fetch a new price observation, persist it, recompute analytics, store
    the resulting prediction/recommendation, and fire alerts if warranted."""
    price, airline = simulate_price(tracker.origin_airport, tracker.destination_airport, tracker.departure_date)

    observation = PriceObservation(
        tracker_id=tracker.id,
        price=price,
        airline=airline,
        timestamp=datetime.utcnow(),
    )
    db.add(observation)
    db.flush()

    observations = list(tracker.observations) + [observation]
    result = run_analytics(observations)
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
        generated_at=datetime.utcnow(),
    )
    db.add(prediction)
    db.commit()

    try:
        alerts.dispatch_alerts(tracker, prediction)
    except Exception:
        logger.exception("Alert dispatch failed for tracker %s", tracker.id)

    return prediction


def process_all_active_trackers(db: Session) -> int:
    trackers = db.query(Tracker).filter(Tracker.active.is_(True)).all()
    count = 0
    for tracker in trackers:
        try:
            process_tracker(db, tracker)
            count += 1
        except Exception:
            logger.exception("Failed to process tracker %s", tracker.id)
            db.rollback()
    return count
