"""Travelpayouts / Aviasales Data API.

Free with a Travelpayouts account. Returns the cheapest real fares that
Aviasales users found for a route and date in the last ~48 hours.
Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163
"""

from __future__ import annotations

from datetime import date

import httpx

from app.services.providers.base import PriceQuote, ProviderError, airline_name

BASE_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"


def fetch_quote(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: date | None,
    *,
    token: str,
    currency: str = "usd",
    market: str = "us",
    client: httpx.Client | None = None,
) -> PriceQuote | None:
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": departure_date.isoformat(),
        "one_way": "false" if return_date else "true",
        "direct": "false",
        "sorting": "price",
        "currency": currency,
        "market": market,
        "limit": 30,
        "page": 1,
    }
    if return_date:
        params["return_at"] = return_date.isoformat()

    own_client = client is None
    client = client or httpx.Client(timeout=20)
    try:
        resp = client.get(
            BASE_URL,
            params=params,
            headers={"X-Access-Token": token, "Accept-Encoding": "gzip, deflate"},
        )
    except httpx.HTTPError as exc:
        raise ProviderError(f"Travelpayouts unreachable: {exc}") from exc
    finally:
        if own_client:
            client.close()

    if resp.status_code == 401:
        raise ProviderError("Travelpayouts rejected the token (401). Check TRAVELPAYOUTS_TOKEN.")
    if resp.status_code == 429:
        raise ProviderError("Travelpayouts rate limit hit (429).")
    if resp.status_code >= 400:
        raise ProviderError(f"Travelpayouts error {resp.status_code}: {resp.text[:200]}")

    body = resp.json()
    if not body.get("success", False):
        raise ProviderError(f"Travelpayouts error: {body.get('error') or 'unknown'}")

    dep = departure_date.isoformat()
    ret = return_date.isoformat() if return_date else None
    offers = []
    for item in body.get("data") or []:
        if not str(item.get("departure_at", "")).startswith(dep):
            continue
        if ret and not str(item.get("return_at", "")).startswith(ret):
            continue
        if item.get("price") is None:
            continue
        offers.append(item)

    if not offers:
        return None

    best = min(offers, key=lambda o: float(o["price"]))
    code = best.get("airline")
    flight_no = best.get("flight_number")
    link = best.get("link")
    return PriceQuote(
        price=round(float(best["price"]), 2),
        airline=airline_name(code),
        source="travelpayouts",
        flight_number=f"{code}{flight_no}" if code and flight_no else None,
        transfers=best.get("transfers"),
        booking_link=f"https://www.aviasales.com{link}" if link else None,
    )
