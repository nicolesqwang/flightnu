from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_or_create_default_user
from app.models.models import PriceObservation, Prediction, Tracker
from app.schemas.schemas import DashboardSummaryOut, TrackerCardOut, TrackerOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    trackers = db.scalars(
        select(Tracker).where(Tracker.user_id == user.id).order_by(Tracker.active.desc(), Tracker.created_at.desc())
    ).all()
    ids = [t.id for t in trackers]

    counts = dict(
        db.execute(
            select(PriceObservation.tracker_id, func.count())
            .where(PriceObservation.tracker_id.in_(ids))
            .group_by(PriceObservation.tracker_id)
        ).all()
    ) if ids else {}

    # Latest prediction per tracker in one query.
    latest_ts = (
        select(Prediction.tracker_id, func.max(Prediction.generated_at).label("ts"))
        .where(Prediction.tracker_id.in_(ids))
        .group_by(Prediction.tracker_id)
        .subquery()
    )
    latest = {
        p.tracker_id: p
        for p in db.scalars(
            select(Prediction).join(
                latest_ts, (Prediction.tracker_id == latest_ts.c.tracker_id) & (Prediction.generated_at == latest_ts.c.ts)
            )
        )
    } if ids else {}

    # Most recent data source per tracker (real provider vs simulator).
    latest_obs_ts = (
        select(PriceObservation.tracker_id, func.max(PriceObservation.timestamp).label("ts"))
        .where(PriceObservation.tracker_id.in_(ids))
        .group_by(PriceObservation.tracker_id)
        .subquery()
    )
    sources = dict(
        db.execute(
            select(PriceObservation.tracker_id, PriceObservation.source).join(
                latest_obs_ts,
                (PriceObservation.tracker_id == latest_obs_ts.c.tracker_id)
                & (PriceObservation.timestamp == latest_obs_ts.c.ts),
            )
        ).all()
    ) if ids else {}

    cards: list[TrackerCardOut] = []
    savings_values: list[float] = []
    confidence_values: list[float] = []
    for tracker in trackers:
        p = latest.get(tracker.id)
        savings = None
        if p:
            savings = max(0.0, p.historical_average - p.current_price)
            if tracker.active:
                savings_values.append(savings)
                if p.has_forecast:
                    confidence_values.append(p.confidence_score)
        cards.append(
            TrackerCardOut(
                tracker=TrackerOut.model_validate(tracker),
                current_price=p.current_price if p else None,
                historical_average=p.historical_average if p else None,
                savings_opportunity=savings,
                confidence_score=p.confidence_score if p and p.has_forecast else None,
                recommendation=p.recommendation if p else None,
                observation_count=counts.get(tracker.id, 0),
                data_source=sources.get(tracker.id),
            )
        )

    return DashboardSummaryOut(
        total_active_trackers=sum(1 for t in trackers if t.active),
        total_observations=sum(counts.values()),
        average_savings_opportunity=(sum(savings_values) / len(savings_values)) if savings_values else 0.0,
        average_prediction_confidence=(sum(confidence_values) / len(confidence_values)) if confidence_values else 0.0,
        tracker_cards=cards,
    )
