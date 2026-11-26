from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import require_cron
from app.models.models import Tracker
from app.schemas.schemas import AirportOut, IngestOut, ServerStatusOut
from app.services.airports import search_airports
from app.services.ingestion import run_due_trackers

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/status", response_model=ServerStatusOut)
def status(db: Session = Depends(get_db)):
    s = get_settings()
    provider = s.price_provider.lower()
    configured = {
        "travelpayouts": bool(s.travelpayouts_token),
        "serpapi": bool(s.serpapi_key),
        "simulator": True,
    }.get(provider, False)
    return ServerStatusOut(
        price_provider=provider,
        provider_configured=configured,
        serpapi_configured=bool(s.serpapi_key),
        admin_key_required=bool(s.admin_key),
        max_active_trackers=s.max_active_trackers,
        active_trackers=db.scalar(select(func.count()).select_from(Tracker).where(Tracker.active.is_(True))) or 0,
        last_ingest_at=db.scalar(select(func.max(Tracker.last_checked_at))),
    )


@router.get("/airports", response_model=list[AirportOut])
def airports(q: str = Query(min_length=1, max_length=40), limit: int = Query(8, ge=1, le=20)):
    return [AirportOut(code=a["code"], name=a["name"], city=a["city"], country=a["country"]) for a in search_airports(q, limit)]


@router.post("/internal/ingest", response_model=IngestOut, dependencies=[Depends(require_cron)])
def ingest(force: bool = False, db: Session = Depends(get_db)):
    """Called by the scheduled GitHub Action. Fetches prices for every tracker
    whose tracking frequency says it is due."""
    summary = run_due_trackers(db, force=force)
    return IngestOut(**summary.__dict__)
