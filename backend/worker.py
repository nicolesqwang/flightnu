import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.core.database import Base, engine
from app.core.scheduler import run_ingestion_job, start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flight_alpha.worker")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    def log_message(self, *args):
        pass


def main():
    Base.metadata.create_all(bind=engine)
    logger.info("Flight Alpha worker starting up")

    run_ingestion_job()
    scheduler = start_scheduler()

    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Worker health server on port %d", port)
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
