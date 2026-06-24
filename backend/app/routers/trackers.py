import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_or_create_default_user
from app.models.models import PriceObservation, Tracker
from app.schemas.schemas import (
    PredictionOut,
    PriceObservationOut,
    TrackerCreate,
    TrackerDetailOut,
    TrackerOut,
)
from app.services.ingestion import process_tracker
from app.services.simulator import simulate_price

router = APIRouter(prefix="/api/trackers", tags=["trackers"])


@router.get("", response_model=list[TrackerOut])
def list_trackers(db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    return db.query(Tracker).filter(Tracker.user_id == user.id).order_by(Tracker.created_at.desc()).all()


@router.post("", response_model=TrackerOut, status_code=201)
def create_tracker(payload: TrackerCreate, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    tracker = Tracker(
        user_id=user.id,
        origin_airport=payload.origin_airport.upper(),
        destination_airport=payload.destination_airport.upper(),
        departure_date=payload.departure_date,
        return_date=payload.return_date,
        tracking_frequency=payload.tracking_frequency,
        alerts_enabled=payload.alerts_enabled,
        discord_webhook_url=payload.discord_webhook_url,
        alert_email=payload.alert_email,
    )
    db.add(tracker)
    db.commit()
    db.refresh(tracker)

    # Seed a handful of historical observations so the dashboard has data immediately.
    rng = random.Random(tracker.id)
    now = datetime.utcnow()
    for i in range(40, 0, -1):
        ts = now - timedelta(hours=i * 4)
        price, airline = simulate_price(
            tracker.origin_airport, tracker.destination_airport, tracker.departure_date, now=ts, rng=rng
        )
        db.add(PriceObservation(tracker_id=tracker.id, price=price, airline=airline, timestamp=ts))
    db.commit()
    db.refresh(tracker)

    process_tracker(db, tracker)
    db.refresh(tracker)
    return tracker


@router.get("/{tracker_id}", response_model=TrackerDetailOut)
def get_tracker(tracker_id: str, db: Session = Depends(get_db)):
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if tracker is None:
        raise HTTPException(status_code=404, detail="Tracker not found")

    observations = [PriceObservationOut.model_validate(o) for o in tracker.observations]
    predictions = [PredictionOut.model_validate(p) for p in tracker.predictions]
    latest = predictions[-1] if predictions else None

    return TrackerDetailOut(
        tracker=TrackerOut.model_validate(tracker),
        observations=observations,
        latest_prediction=latest,
        prediction_history=predictions,
    )


@router.post("/{tracker_id}/refresh", response_model=PredictionOut)
def refresh_tracker(tracker_id: str, db: Session = Depends(get_db)):
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if tracker is None:
        raise HTTPException(status_code=404, detail="Tracker not found")
    prediction = process_tracker(db, tracker)
    if prediction is None:
        raise HTTPException(status_code=400, detail="Unable to generate prediction")
    return prediction


@router.patch("/{tracker_id}", response_model=TrackerOut)
def update_tracker(tracker_id: str, active: bool | None = None, db: Session = Depends(get_db)):
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if tracker is None:
        raise HTTPException(status_code=404, detail="Tracker not found")
    if active is not None:
        tracker.active = active
    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete("/{tracker_id}", status_code=204)
def delete_tracker(tracker_id: str, db: Session = Depends(get_db)):
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if tracker is None:
        raise HTTPException(status_code=404, detail="Tracker not found")
    db.delete(tracker)
    db.commit()
