"""In-process scheduler for running FlightNu on your own machine or a paid
always-on host. In the free Render setup, the GitHub Action in
.github/workflows/ingest.yml calls POST /api/internal/ingest instead."""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.database import SessionLocal
from app.services.ingestion import run_due_trackers

logger = logging.getLogger("flightnu.scheduler")


def run_ingestion_job() -> None:
    db = SessionLocal()
    try:
        summary = run_due_trackers(db)
        logger.info(
            "Ingest: checked=%d fetched=%d not_due=%d deactivated=%d errors=%d",
            summary.checked, summary.fetched, summary.skipped_not_due, summary.deactivated, len(summary.errors),
        )
        for err in summary.errors:
            logger.warning("  %s", err)
    finally:
        db.close()


def run_forever() -> None:
    # Checks every 15 minutes; each tracker is fetched only when its own
    # frequency (hourly / every 4 hours / daily) says it is due.
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_ingestion_job, "interval", minutes=15, id="flight_price_ingestion")
    run_ingestion_job()
    scheduler.start()
