# FlightNu

Flight price intelligence and prediction platform. Tracks flight prices over time, runs statistical analysis and forecasting, and recommends whether to buy now, wait, or keep monitoring.

```
Frontend (Next.js)
      |
FastAPI REST API
      |
PostgreSQL
      |
Background Worker (APScheduler)
      |
Price Simulator -> Analytics Engine -> Predictions & Alerts
```

## Stack

- **Frontend**: Next.js (App Router), TypeScript, TailwindCSS, Recharts
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL (SQLite for local dev by default)
- **Background jobs**: APScheduler, running as a separate worker process
- **Deployment**: Render (`render.yaml` blueprint — web service + worker + Postgres + frontend)

## Price data

There's no live flight-price API wired up. `backend/app/services/simulator.py` generates statistically realistic synthetic prices (route-distance-based base fare, day/hour seasonality, days-to-departure urgency curve, random walk + volatility spikes) so the full ingestion → analytics → prediction pipeline runs end-to-end without API keys. Swapping in a real provider (Amadeus, Skyscanner, etc.) later only requires replacing `simulate_price()` in that file.

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py        # creates 3 sample trackers (SFO->JFK, SMF->SEA, LAX->HNL) with history
uvicorn app.main:app --reload --port 8123
```

Runs on `http://localhost:8123`. Defaults to a local SQLite file (`flightnu.db`) — set `DATABASE_URL` in `backend/.env` (see `.env.example`) to point at Postgres instead.

To run the background ingestion loop locally (separate from the API process):

```bash
cd backend && source .venv/bin/activate
python worker.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:3000` (or next available port). Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to point at the backend (defaults to `http://localhost:8123`).

## Deployment (Render)

`render.yaml` defines four resources as a single blueprint:

- `flightnu-db` — Postgres
- `flightnu-api` — FastAPI web service
- `flightnu-worker` — background worker running the 4-hour ingestion cycle
- `flightnu-web` — Next.js frontend

Push to a connected repo and use Render's "New Blueprint" flow to provision all four from `render.yaml`. Set `DISCORD_WEBHOOK_URL` / SMTP secrets on the `flightnu-api` and `flightnu-worker` services if you want default alert delivery (trackers can also set a per-tracker Discord webhook / email at creation time).

## Notes

- Single-user mode: there's no login yet — all trackers belong to one implicit demo user (`backend/app/core/deps.py`). Auth can be layered in later without touching the data model.
- Recommendation logic (`backend/app/services/analytics.py`): **BUY_NOW** requires z-score < -2, confidence > 80%, and a rising 48h forecast; **WAIT** triggers when confidence < 60% or the forecast points down; everything else is **MONITOR**.
