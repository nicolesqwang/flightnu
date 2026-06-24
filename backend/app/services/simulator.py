"""Synthetic flight price generator.

Stands in for a real flight-price API (Amadeus, Skyscanner, etc). It produces
statistically realistic observations -- base fare by route, day/hour
seasonality, a slow trend as departure approaches, and random volatility --
so the ingestion -> analytics -> prediction pipeline can run end-to-end.
Swapping in a real provider later only requires replacing `fetch_price`.
"""

from __future__ import annotations

import hashlib
import math
import random
from datetime import date, datetime

AIRLINES = [
    "United",
    "Delta",
    "American",
    "Southwest",
    "JetBlue",
    "Alaska",
    "Spirit",
]

_AIRPORT_COORDS = {
    "SFO": (37.6, -122.4), "JFK": (40.6, -73.8), "LAX": (33.9, -118.4),
    "SMF": (38.7, -121.6), "SEA": (47.4, -122.3), "HNL": (21.3, -157.9),
    "ORD": (41.9, -87.9), "ATL": (33.6, -84.4), "BOS": (42.4, -71.0),
    "DFW": (32.9, -97.0), "DEN": (39.8, -104.7), "MIA": (25.8, -80.3),
    "EWR": (40.7, -74.2), "LAS": (36.1, -115.2), "PHX": (33.4, -112.0),
    "AUS": (30.2, -97.7), "MCO": (28.4, -81.3), "SAN": (32.7, -117.2),
}


def _haversine_miles(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(h))


def _route_distance(origin: str, destination: str) -> float:
    if origin in _AIRPORT_COORDS and destination in _AIRPORT_COORDS:
        return _haversine_miles(_AIRPORT_COORDS[origin], _AIRPORT_COORDS[destination])
    # deterministic pseudo-distance fallback for unknown airport codes
    seed = int(hashlib.sha256(f"{origin}{destination}".encode()).hexdigest(), 16)
    return 400 + (seed % 2600)


def _base_fare(origin: str, destination: str) -> float:
    distance = _route_distance(origin, destination)
    return 60 + distance * 0.11


def _route_seed(origin: str, destination: str, departure_date: date) -> int:
    key = f"{origin}-{destination}-{departure_date.isoformat()}"
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)


def simulate_price(
    origin: str,
    destination: str,
    departure_date: date,
    now: datetime | None = None,
    rng: random.Random | None = None,
) -> tuple[float, str]:
    """Generate one synthetic (price, airline) observation for a route."""
    now = now or datetime.utcnow()
    rng = rng or random.Random(_route_seed(origin, destination, departure_date) ^ int(now.timestamp() // 60))

    base = _base_fare(origin, destination)

    days_out = max((departure_date - now.date()).days, 0)
    if days_out > 60:
        urgency_mult = 0.85
    elif days_out > 21:
        urgency_mult = 0.95
    elif days_out > 7:
        urgency_mult = 1.1
    elif days_out > 2:
        urgency_mult = 1.35
    else:
        urgency_mult = 1.65

    dow_mult = {0: 1.05, 1: 0.95, 2: 0.92, 3: 0.97, 4: 1.15, 5: 1.2, 6: 1.08}[now.weekday()]
    hour_mult = 1.0 + 0.08 * math.sin((now.hour - 9) / 24 * 2 * math.pi)

    trend_progress = 1 - (days_out / 120) if days_out < 120 else 0
    long_trend = 1 + 0.18 * trend_progress

    noise = rng.gauss(0, 0.06)
    spike = 0.0
    if rng.random() < 0.05:
        spike = rng.choice([-1, 1]) * rng.uniform(0.15, 0.35)

    price = base * urgency_mult * dow_mult * hour_mult * long_trend * (1 + noise + spike)
    price = max(price, base * 0.4)

    airline = rng.choice(AIRLINES)
    return round(price, 2), airline
