import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.ingestion import process_all_active_trackers

logger = logging.getLogger("flightnu.scheduler")


def run_ingestion_job() -> None:
    db = SessionLocal()
    try:
        count = process_all_active_trackers(db)
        logger.info("Ingestion job processed %d trackers", count)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_ingestion_job,
        "interval",
        hours=settings.ingestion_interval_hours,
        id="flight_price_ingestion",
    )
    scheduler.start()
    return scheduler
