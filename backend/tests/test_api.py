from datetime import timedelta

from app.core.timeutil import utctoday

ADMIN = {"X-Admin-Key": "test-admin"}


def _payload(**kw):
    body = {
        "origin_airport": "sfo",
        "destination_airport": "JFK",
        "departure_date": (utctoday() + timedelta(days=40)).isoformat(),
        "tracking_frequency": "EVERY_4_HOURS",
        "alerts_enabled": False,
    }
    body.update(kw)
    return body


def test_create_and_read_tracker(client):
    r = client.post("/api/trackers", json=_payload())
    assert r.status_code == 201, r.text
    t = r.json()
    assert t["origin_airport"] == "SFO"
    assert t["created_at"].endswith("Z")

    d = client.get(f"/api/trackers/{t['id']}").json()
    assert d["total_observations"] == 1  # one real reading, no invented history
    assert d["observations"][0]["source"] == "simulator"
    assert d["observations"][0]["timestamp"].endswith("Z")
    assert d["latest_prediction"]["has_forecast"] is False

    s = client.get("/api/dashboard/summary").json()
    assert s["total_active_trackers"] == 1
    assert s["tracker_cards"][0]["data_source"] == "simulator"


def test_validation_rejects_bad_input(client):
    cases = [
        _payload(origin_airport="XYZ"),
        _payload(destination_airport="SFO"),
        _payload(departure_date=(utctoday() - timedelta(days=1)).isoformat()),
        _payload(return_date=utctoday().isoformat()),
        _payload(discord_webhook_url="https://evil.example.com/hook"),
    ]
    for body in cases:
        assert client.post("/api/trackers", json=body).status_code == 422, body


def test_duplicate_trip_rejected(client):
    assert client.post("/api/trackers", json=_payload()).status_code == 201
    assert client.post("/api/trackers", json=_payload()).status_code == 409


def test_refresh_is_rate_limited(client):
    tid = client.post("/api/trackers", json=_payload()).json()["id"]
    r = client.post(f"/api/trackers/{tid}/refresh")
    assert r.status_code == 429  # just fetched at creation


def test_delete_requires_admin_key(client):
    tid = client.post("/api/trackers", json=_payload()).json()["id"]
    assert client.delete(f"/api/trackers/{tid}").status_code == 401
    assert client.patch(f"/api/trackers/{tid}?active=false").status_code == 401
    assert client.delete(f"/api/trackers/{tid}", headers=ADMIN).status_code == 204


def test_cron_ingest(client):
    client.post("/api/trackers", json=_payload())
    assert client.post("/api/internal/ingest").status_code == 401
    r = client.post("/api/internal/ingest", headers={"X-Cron-Secret": "test-cron"})
    assert r.status_code == 200
    assert r.json()["skipped_not_due"] == 1  # checked moments ago
    r = client.post("/api/internal/ingest?force=true", headers={"X-Cron-Secret": "test-cron"})
    assert r.json()["fetched"] == 1


def test_status_and_airports(client):
    s = client.get("/api/status").json()
    assert s["price_provider"] == "simulator"
    assert s["admin_key_required"] is True
    a = client.get("/api/airports", params={"q": "NRT"}).json()
    assert a[0]["code"] == "NRT"
