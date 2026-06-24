"""Seeds sample trackers (SFO->JFK, SMF->SEA, LAX->HNL) with historical
observations and predictions so the dashboard has data to show immediately."""

import random
from datetime import date, datetime, timedelta

from app.core.database import Base, SessionLocal, engine
from app.core.deps import get_or_create_default_user
from app.models.models import PriceObservation, Tracker
from app.services.ingestion import process_tracker
from app.services.simulator import simulate_price

SAMPLE_ROUTES = [
    ("SFO", "JFK", 45),
    ("SMF", "SEA", 20),
    ("LAX", "HNL", 75),
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        if db.query(Tracker).filter(Tracker.user_id == user.id).count() > 0:
            print("Trackers already exist, skipping seed.")
            return

        now = datetime.utcnow()
        for origin, destination, days_until_departure in SAMPLE_ROUTES:
            departure = date.today() + timedelta(days=days_until_departure)
            tracker = Tracker(
                user_id=user.id,
                origin_airport=origin,
                destination_airport=destination,
                departure_date=departure,
                alerts_enabled=True,
            )
            db.add(tracker)
            db.commit()
            db.refresh(tracker)

            rng = random.Random(tracker.id)
            for i in range(120, 0, -1):
                ts = now - timedelta(hours=i * 4)
                price, airline = simulate_price(origin, destination, departure, now=ts, rng=rng)
                db.add(PriceObservation(tracker_id=tracker.id, price=price, airline=airline, timestamp=ts))
            db.commit()
            db.refresh(tracker)

            process_tracker(db, tracker)
            print(f"Seeded {origin} -> {destination} with {len(tracker.observations)} observations")
    finally:
        db.close()


if __name__ == "__main__":
    main()
