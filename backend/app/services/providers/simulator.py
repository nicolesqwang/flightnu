"""Synthetic fares for offline demos and tests ONLY (PRICE_PROVIDER=simulator).

Every observation it produces is stored with source="simulator" and the UI
labels it as simulated. It is never used as a silent fallback for real data.
Prices follow a mean-reverting random walk (prices drift; they do not jump
independently every reading) around a distance-based fare that rises as
departure approaches, with one consistent airline per route.
"""

from __future__ import annotations

import hashlib
import random
from datetime import date, datetime

from app.core.timeutil import utcnow
from app.services.airports import distance_miles
from app.services.providers.base import PriceQuote

_AIRLINES = ["United", "Delta", "American", "Alaska", "Southwest", "JetBlue"]


def _seed(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest(), 16) % (2**32)


def fair_value(origin: str, destination: str, departure_date: date, now: datetime) -> float:
    miles = distance_miles(origin, destination) or 1000.0
    base = 50 + 0.12 * miles if miles < 3000 else 200 + 0.08 * miles
    days_out = max((departure_date - now.date()).days, 0)
    # Fares bottom out ~6-8 weeks before departure, then climb.
    if days_out > 90:
        mult = 1.05
    elif days_out > 45:
        mult = 0.95
    elif days_out > 21:
        mult = 1.0
    elif days_out > 7:
        mult = 1.15
    else:
        mult = 1.4
    return base * mult


def quote(
    origin: str,
    destination: str,
    departure_date: date,
    *,
    previous_price: float | None = None,
    now: datetime | None = None,
    rng: random.Random | None = None,
) -> PriceQuote:
    now = now or utcnow()
    rng = rng or random.Random(_seed(origin, destination, departure_date.isoformat(), now.isoformat()))
    target = fair_value(origin, destination, departure_date, now)
    start = previous_price if previous_price is not None else target
    # Mean reversion toward the fair value + small step + rare fare-sale shock.
    step = 0.15 * (target - start) + rng.gauss(0, 0.02) * target
    if rng.random() < 0.03:
        step += rng.choice([-1, 1]) * rng.uniform(0.08, 0.18) * target
    price = max(target * 0.5, start + step)
    airline = _AIRLINES[_seed(origin, destination) % len(_AIRLINES)]
    return PriceQuote(price=round(price, 2), airline=airline, source="simulator")
