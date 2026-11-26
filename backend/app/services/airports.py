"""Airport lookup backed by OurAirports data (public domain): every airport
with scheduled passenger service and an IATA code (~4,000 airports)."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "airports.json"


@lru_cache
def _airports() -> dict[str, dict]:
    with _DATA.open(encoding="utf-8") as f:
        return json.load(f)


def get_airport(code: str) -> dict | None:
    return _airports().get(code.upper())


def is_valid_airport(code: str) -> bool:
    return get_airport(code) is not None


def search_airports(query: str, limit: int = 10) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    exact, prefix, contains = [], [], []
    for code, a in _airports().items():
        item = {"code": code, **a}
        if code.lower() == q:
            exact.append(item)
        elif code.lower().startswith(q) or a["city"].lower().startswith(q):
            prefix.append(item)
        elif q in a["name"].lower() or q in a["city"].lower():
            contains.append(item)
    return (exact + prefix + contains)[:limit]


def distance_miles(origin: str, destination: str) -> float | None:
    a, b = get_airport(origin), get_airport(destination)
    if not a or not b:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(h))
