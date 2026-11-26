import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.routers import dashboard, meta, trackers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flightnu")

settings = get_settings()


def _seed_in_background() -> None:
    from app.services.seed import seed_demo_trackers

    db = SessionLocal()
    try:
        created = seed_demo_trackers(db)
        if created:
            logger.info("Seeded %d demo trackers", created)
    except Exception:
        logger.exception("Demo seeding failed")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.auto_seed:
        # Don't block startup on network calls to the price provider.
        threading.Thread(target=_seed_in_background, daemon=True).start()
    yield


app = FastAPI(title="FlightNu API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trackers.router)
app.include_router(dashboard.router)
app.include_router(meta.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
