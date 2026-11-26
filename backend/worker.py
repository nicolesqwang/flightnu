"""Local background worker: `python worker.py` keeps fetching prices on schedule.

Not used on Render's free plan (free web services sleep after 15 idle
minutes). There, .github/workflows/ingest.yml triggers ingestion instead.
"""

import logging

from app.core.database import init_db
from app.core.scheduler import run_forever

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    init_db()
    logging.getLogger("flightnu.worker").info("FlightNu worker starting")
    run_forever()
