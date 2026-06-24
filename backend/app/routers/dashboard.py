from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_or_create_default_user
from app.models.models import PriceObservation, Tracker
from app.schemas.schemas import DashboardSummaryOut, TrackerCardOut, TrackerOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    trackers = db.query(Tracker).filter(Tracker.user_id == user.id).order_by(Tracker.created_at.desc()).all()

    total_observations = (
        db.query(PriceObservation)
        .join(Tracker)
        .filter(Tracker.user_id == user.id)
        .count()
    )

    cards: list[TrackerCardOut] = []
    savings_values: list[float] = []
    confidence_values: list[float] = []

    for tracker in trackers:
        latest_prediction = tracker.predictions[-1] if tracker.predictions else None
        savings = None
        if latest_prediction:
            savings = max(0.0, latest_prediction.historical_average - latest_prediction.current_price)
            savings_values.append(savings)
            confidence_values.append(latest_prediction.confidence_score)

        cards.append(
            TrackerCardOut(
                tracker=TrackerOut.model_validate(tracker),
                current_price=latest_prediction.current_price if latest_prediction else None,
                historical_average=latest_prediction.historical_average if latest_prediction else None,
                savings_opportunity=savings,
                confidence_score=latest_prediction.confidence_score if latest_prediction else None,
                recommendation=latest_prediction.recommendation if latest_prediction else None,
                observation_count=len(tracker.observations),
            )
        )

    return DashboardSummaryOut(
        total_active_trackers=sum(1 for t in trackers if t.active),
        total_observations=total_observations,
        average_savings_opportunity=(sum(savings_values) / len(savings_values)) if savings_values else 0.0,
        average_prediction_confidence=(sum(confidence_values) / len(confidence_values)) if confidence_values else 0.0,
        tracker_cards=cards,
    )
