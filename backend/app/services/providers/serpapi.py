"""Google Flights via SerpApi (free plan: 250 searches/month).

Live Google Flights results plus `price_insights.price_history`, a real
~60-day price history for the route, used to backfill new trackers.
Docs: https://serpapi.com/google-flights-api
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

import httpx

from app.services.providers.base import PriceQuote, ProviderError

BASE_URL = "https://serpapi.com/search.json"


@dataclass
class SerpApiResult:
    quote: PriceQuote | None
    history: list[PriceQuote] = field(default_factory=list)
    typical_range: tuple[float, float] | None = None


def fetch(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: date | None,
    *,
    api_key: str,
    currency: str = "usd",
    client: httpx.Client | None = None,
) -> SerpApiResult:
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date.isoformat(),
        "type": "1" if return_date else "2",
        "currency": currency.upper(),
        "hl": "en",
        "gl": "us",
        "api_key": api_key,
    }
    if return_date:
        params["return_date"] = return_date.isoformat()

    own_client = client is None
    client = client or httpx.Client(timeout=60)
    try:
        resp = client.get(BASE_URL, params=params)
    except httpx.HTTPError as exc:
        raise ProviderError(f"SerpApi unreachable: {exc}") from exc
    finally:
        if own_client:
            client.close()

    if resp.status_code == 401:
        raise ProviderError("SerpApi rejected the key (401). Check SERPAPI_KEY.")
    if resp.status_code == 429:
        raise ProviderError("SerpApi monthly search quota used up (429).")
    if resp.status_code >= 400:
        raise ProviderError(f"SerpApi error {resp.status_code}: {resp.text[:200]}")

    body = resp.json()
    if body.get("error"):
        # "Google Flights hasn't returned any results" is a normal empty result.
        if "hasn't returned any results" in body["error"]:
            return SerpApiResult(quote=None)
        raise ProviderError(f"SerpApi error: {body['error']}")

    offers = [o for o in (body.get("best_flights") or []) + (body.get("other_flights") or []) if o.get("price")]
    quote = None
    if offers:
        best = min(offers, key=lambda o: float(o["price"]))
        legs = best.get("flights") or []
        airlines = []
        for leg in legs:
            name = leg.get("airline")
            if name and name not in airlines:
                airlines.append(name)
        quote = PriceQuote(
            price=round(float(best["price"]), 2),
            airline=" / ".join(airlines) or "Unknown",
            source="serpapi",
            flight_number=legs[0].get("flight_number") if legs else None,
            transfers=max(0, len(legs) - 1),
            booking_link=(body.get("search_metadata") or {}).get("google_flights_url"),
        )

    insights = body.get("price_insights") or {}
    history: list[PriceQuote] = []
    for point in insights.get("price_history") or []:
        try:
            ts, price = int(point[0]), float(point[1])
        except (TypeError, ValueError, IndexError):
            continue
        history.append(
            PriceQuote(
                price=price,
                airline="Google Flights (lowest)",
                source="serpapi_history",
                observed_at=datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None),
            )
        )

    typical = insights.get("typical_price_range")
    typical_range = (float(typical[0]), float(typical[1])) if typical and len(typical) == 2 else None
    return SerpApiResult(quote=quote, history=history, typical_range=typical_range)
