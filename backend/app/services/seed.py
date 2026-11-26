"""Demo trackers so a fresh deployment isn't empty. Real prices only: the
trackers are created, then filled by the provider (no invented history)."""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_or_create_default_user
from app.core.timeutil import utctoday
from app.models.models import Tracker
from app.services.ingestion import initialize_tracker

logger = logging.getLogger("flightnu.seed")

DEMO_ROUTES = [
    ("SFO", "JFK", 45),
    ("LAX", "HNL", 75),
    ("JFK", "LAX", 30),
]


def seed_demo_trackers(db: Session) -> int:
    if (db.scalar(select(func.count()).select_from(Tracker)) or 0) > 0:
        return 0
    user = get_or_create_default_user(db)
    created = 0
    for origin, destination, days in DEMO_ROUTES:
        tracker = Tracker(
            user_id=user.id,
            origin_airport=origin,
            destination_airport=destination,
            departure_date=utctoday() + timedelta(days=days),
            alerts_enabled=False,
        )
        db.add(tracker)
        db.commit()
        db.refresh(tracker)
        try:
            initialize_tracker(db, tracker)
        except Exception:
            logger.exception("Initial fetch failed for demo tracker %s-%s", origin, destination)
            db.rollback()
        created += 1
    return created
