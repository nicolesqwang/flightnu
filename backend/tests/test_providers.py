from datetime import date

import httpx
import pytest

from app.services.providers import serpapi, travelpayouts
from app.services.providers.base import ProviderError


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_travelpayouts_picks_cheapest_matching_date():
    def handler(request: httpx.Request):
        assert request.headers["X-Access-Token"] == "tok"
        assert request.url.params["departure_at"] == "2027-01-09"
        assert request.url.params["one_way"] == "true"
        return httpx.Response(200, json={
            "success": True, "error": None, "currency": "usd",
            "data": [
                {"price": 289, "airline": "B6", "flight_number": "915", "departure_at": "2027-01-09T07:00:00-08:00",
                 "transfers": 0, "link": "/search/SFO0901JFK1"},
                {"price": 199, "airline": "UA", "flight_number": "1", "departure_at": "2027-01-10T07:00:00-08:00",
                 "transfers": 0, "link": "/search/x"},
                {"price": 312, "airline": "DL", "flight_number": "2", "departure_at": "2027-01-09T09:00:00-08:00",
                 "transfers": 1, "link": "/search/y"},
            ],
        })

    q = travelpayouts.fetch_quote("SFO", "JFK", date(2027, 1, 9), None, token="tok", client=_client(handler))
    assert q.price == 289
    assert q.airline == "JetBlue"
    assert q.flight_number == "B6915"
    assert q.booking_link == "https://www.aviasales.com/search/SFO0901JFK1"
    assert q.source == "travelpayouts"


def test_travelpayouts_no_fare_returns_none():
    handler = lambda r: httpx.Response(200, json={"success": True, "data": [], "error": None})
    assert travelpayouts.fetch_quote("SFO", "JFK", date(2027, 1, 9), None, token="t", client=_client(handler)) is None


def test_travelpayouts_bad_token_raises():
    handler = lambda r: httpx.Response(401, json={"success": False})
    with pytest.raises(ProviderError):
        travelpayouts.fetch_quote("SFO", "JFK", date(2027, 1, 9), None, token="bad", client=_client(handler))


def test_serpapi_quote_and_history():
    def handler(request: httpx.Request):
        assert request.url.params["engine"] == "google_flights"
        assert request.url.params["type"] == "2"
        return httpx.Response(200, json={
            "best_flights": [
                {"price": 318, "flights": [{"airline": "Alaska", "flight_number": "AS 1"}, {"airline": "Alaska", "flight_number": "AS 2"}]},
            ],
            "other_flights": [{"price": 344, "flights": [{"airline": "Delta", "flight_number": "DL 9"}]}],
            "price_insights": {"lowest_price": 318, "typical_price_range": [290, 420],
                               "price_history": [[1761955200, 355], [1762041600, 340]]},
        })

    r = serpapi.fetch("SFO", "JFK", date(2027, 1, 9), None, api_key="k", client=_client(handler))
    assert r.quote.price == 318
    assert r.quote.airline == "Alaska"
    assert r.quote.transfers == 1
    assert [p.price for p in r.history] == [355, 340]
    assert r.typical_range == (290, 420)
