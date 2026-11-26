"""Chooses a price provider for a tracker and returns one real quote."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import get_settings
from app.models.models import Tracker
from app.services.providers import serpapi, simulator, travelpayouts
from app.services.providers.base import PriceQuote, ProviderError

logger = logging.getLogger("flightnu.pricing")


@dataclass
class FetchOutcome:
    quote: PriceQuote | None
    error: str | None = None


def fetch_current_price(tracker: Tracker, previous_price: float | None = None) -> FetchOutcome:
    s = get_settings()
    provider = s.price_provider.lower()
    args = (tracker.origin_airport, tracker.destination_airport, tracker.departure_date, tracker.return_date)

    if provider == "simulator":
        return FetchOutcome(simulator.quote(*args[:3], previous_price=previous_price))

    errors: list[str] = []

    if provider == "travelpayouts":
        if not s.travelpayouts_token:
            errors.append("TRAVELPAYOUTS_TOKEN is not set on the server.")
        else:
            try:
                q = travelpayouts.fetch_quote(
                    *args, token=s.travelpayouts_token, currency=s.currency, market=s.travelpayouts_market
                )
                if q:
                    return FetchOutcome(q)
                errors.append("No fare cached by Aviasales for this exact route and date yet.")
            except ProviderError as exc:
                errors.append(str(exc))

    use_serpapi = provider == "serpapi" or (s.serpapi_fallback and provider == "travelpayouts")
    if use_serpapi and s.serpapi_key:
        try:
            result = serpapi.fetch(*args, api_key=s.serpapi_key, currency=s.currency)
            if result.quote:
                return FetchOutcome(result.quote)
            errors.append("Google Flights returned no offers for this route and date.")
        except ProviderError as exc:
            errors.append(str(exc))
    elif provider == "serpapi":
        errors.append("SERPAPI_KEY is not set on the server.")

    if provider not in ("travelpayouts", "serpapi"):
        errors.append(f"Unknown PRICE_PROVIDER '{s.price_provider}'.")

    message = " ".join(errors) or "No price available."
    logger.info("No price for tracker %s: %s", tracker.id, message)
    return FetchOutcome(None, message)


def fetch_history(tracker: Tracker) -> list[PriceQuote]:
    """Real historical lowest prices (Google Flights price_insights), used once
    when a tracker is created. Returns [] when SerpApi isn't configured."""
    s = get_settings()
    if not (s.serpapi_key and s.serpapi_backfill_on_create) or s.price_provider == "simulator":
        return []
    try:
        result = serpapi.fetch(
            tracker.origin_airport,
            tracker.destination_airport,
            tracker.departure_date,
            tracker.return_date,
            api_key=s.serpapi_key,
            currency=s.currency,
        )
    except ProviderError as exc:
        logger.warning("History backfill failed for %s: %s", tracker.id, exc)
        return []
    points = list(result.history)
    if result.quote:
        points.append(result.quote)
    return points
