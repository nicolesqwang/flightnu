"""Creates demo trackers (SFO->JFK, LAX->HNL, JFK->LAX) on an empty database
and fetches their first real prices. The API also does this automatically
on startup when AUTO_SEED=true."""

import logging

from app.core.database import SessionLocal, init_db
from app.services.seed import seed_demo_trackers

logging.basicConfig(level=logging.INFO)


def main():
    init_db()
    db = SessionLocal()
    try:
        created = seed_demo_trackers(db)
        print(f"Created {created} demo trackers." if created else "Trackers already exist, skipping seed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
