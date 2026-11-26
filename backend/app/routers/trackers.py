from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_or_create_default_user
from app.core.security import require_admin
from app.core.timeutil import utcnow
from app.models.models import PriceObservation, Prediction, Tracker
from app.schemas.schemas import (
    PredictionOut,
    PriceObservationOut,
    TrackerCreate,
    TrackerDetailOut,
    TrackerOut,
)
from app.services.ingestion import fetch_and_update, initialize_tracker

router = APIRouter(prefix="/api/trackers", tags=["trackers"])

MAX_OBSERVATIONS_RETURNED = 1000
MAX_PREDICTIONS_RETURNED = 50


def _get_tracker(db: Session, tracker_id: str) -> Tracker:
    tracker = db.get(Tracker, tracker_id)
    if tracker is None:
        raise HTTPException(status_code=404, detail="Tracker not found")
    return tracker


@router.get("", response_model=list[TrackerOut])
def list_trackers(db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    return db.scalars(select(Tracker).where(Tracker.user_id == user.id).order_by(Tracker.created_at.desc())).all()


@router.post("", response_model=TrackerOut, status_code=201)
def create_tracker(payload: TrackerCreate, db: Session = Depends(get_db)):
    settings = get_settings()
    user = get_or_create_default_user(db)
    active = db.scalar(select(func.count()).select_from(Tracker).where(Tracker.active.is_(True))) or 0
    if active >= settings.max_active_trackers:
        raise HTTPException(
            status_code=409,
            detail=f"This demo is limited to {settings.max_active_trackers} active trackers to stay within free API limits.",
        )
    duplicate = db.scalar(
        select(Tracker).where(
            Tracker.active.is_(True),
            Tracker.origin_airport == payload.origin_airport,
            Tracker.destination_airport == payload.destination_airport,
            Tracker.departure_date == payload.departure_date,
            Tracker.return_date.is_(None) if payload.return_date is None else Tracker.return_date == payload.return_date,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="A tracker for this exact trip already exists.")

    tracker = Tracker(
        user_id=user.id,
        origin_airport=payload.origin_airport,
        destination_airport=payload.destination_airport,
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

    initialize_tracker(db, tracker)
    db.refresh(tracker)
    return tracker


@router.get("/{tracker_id}", response_model=TrackerDetailOut)
def get_tracker(
    tracker_id: str,
    limit: int = Query(MAX_OBSERVATIONS_RETURNED, ge=1, le=MAX_OBSERVATIONS_RETURNED),
    db: Session = Depends(get_db),
):
    tracker = _get_tracker(db, tracker_id)
    total = db.scalar(select(func.count()).select_from(PriceObservation).where(PriceObservation.tracker_id == tracker.id)) or 0
    recent_obs = db.scalars(
        select(PriceObservation)
        .where(PriceObservation.tracker_id == tracker.id)
        .order_by(PriceObservation.timestamp.desc())
        .limit(limit)
    ).all()
    recent_preds = db.scalars(
        select(Prediction)
        .where(Prediction.tracker_id == tracker.id)
        .order_by(Prediction.generated_at.desc())
        .limit(MAX_PREDICTIONS_RETURNED)
    ).all()
    predictions = [PredictionOut.model_validate(p) for p in reversed(recent_preds)]
    return TrackerDetailOut(
        tracker=TrackerOut.model_validate(tracker),
        observations=[PriceObservationOut.model_validate(o) for o in reversed(recent_obs)],
        latest_prediction=predictions[-1] if predictions else None,
        prediction_history=predictions,
        total_observations=total,
    )


@router.post("/{tracker_id}/refresh", response_model=TrackerOut)
def refresh_tracker(tracker_id: str, db: Session = Depends(get_db)):
    """Fetch a real price right now (rate-limited per tracker)."""
    tracker = _get_tracker(db, tracker_id)
    cooldown = timedelta(seconds=get_settings().refresh_cooldown_seconds)
    now = utcnow()
    if tracker.last_checked_at and now - tracker.last_checked_at < cooldown:
        wait = int((cooldown - (now - tracker.last_checked_at)).total_seconds() // 60) + 1
        raise HTTPException(status_code=429, detail=f"Prices were checked recently. Try again in about {wait} min.")
    if tracker.departure_date < now.date():
        raise HTTPException(status_code=400, detail="This flight has already departed.")
    fetch_and_update(db, tracker, now)
    db.refresh(tracker)
    return tracker


@router.patch("/{tracker_id}", response_model=TrackerOut, dependencies=[Depends(require_admin)])
def update_tracker(tracker_id: str, active: bool | None = None, db: Session = Depends(get_db)):
    tracker = _get_tracker(db, tracker_id)
    if active is not None:
        tracker.active = active
    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete("/{tracker_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_tracker(tracker_id: str, db: Session = Depends(get_db)):
    tracker = _get_tracker(db, tracker_id)
    db.delete(tracker)
    db.commit()
