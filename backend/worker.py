"""Standalone entrypoint for the Render background worker service.

Runs the APScheduler ingestion job on a fixed interval (default: every 4
hours, see INGESTION_INTERVAL_HOURS) and then idles. Deployed as a separate
Render "Background Worker" service from the FastAPI web service.
"""

import logging
import time

from app.core.database import Base, engine
from app.core.scheduler import run_ingestion_job, start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flightnu.worker")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("FlightNu worker starting up")

    # Run once immediately on boot so trackers don't sit idle for a full interval.
    run_ingestion_job()

    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
