# FlightNu

Flight price intelligence. Tracks **real** airfares for a route over time, runs statistical analysis and a trend forecast, and recommends whether to buy now, wait, or keep monitoring.

```
Browser ──> flightnu-web (Next.js, Render free)
   │
   └─ JSON ─> flightnu-api (FastAPI, Render free) ──> Neon Postgres (free, no expiry)
                  ▲          │
                  │          └─> Travelpayouts / Aviasales Data API (real fares, free)
                  │          └─> SerpApi Google Flights (optional, 250 free searches/month)
   GitHub Actions (hourly) ── POST /api/internal/ingest
```

## Stack

- **Frontend**: Next.js 16 (App Router), TypeScript, TailwindCSS, Recharts
- **Backend**: FastAPI, SQLAlchemy 2, Pydantic, NumPy
- **Database**: PostgreSQL (Neon free tier in production; SQLite locally)
- **Scheduling**: GitHub Actions cron → `/api/internal/ingest` (free). `python worker.py` runs an APScheduler loop for local / always-on hosting.
- **Price data**: Travelpayouts (Aviasales Data API) by default; SerpApi Google Flights as fallback and for price-history backfill.

## Where prices come from

| Provider | Cost | What it returns |
| --- | --- | --- |
| Travelpayouts / Aviasales (`PRICE_PROVIDER=travelpayouts`, default) | Free account | Cheapest real fares Aviasales users found for the exact route + date in the last ~48h, with airline, flight number, stops and a booking link. Popular routes are well covered; obscure routes/dates may have no cached fare yet. |
| SerpApi Google Flights (`SERPAPI_KEY`) | Free plan: 250 searches/month | Live Google Flights offers + ~60 days of real price history (`price_insights.price_history`). Used once per new tracker to backfill history, and when Aviasales has nothing cached. |
| Simulator (`PRICE_PROVIDER=simulator`) | — | Synthetic data for offline demos/tests only. Every observation is stored with `source=simulator` and labelled "Simulated" in the UI. Never used as a silent fallback. |

Each observation records its `source`, so real and simulated data can never be confused.

## Analytics (`backend/app/services/analytics.py`)

- Descriptive stats: average, low, high, sample std dev, z-score, percentile ("cheaper than X% of prices seen").
- SMA(5) and EWMA(α=0.3) overlays.
- **Forecast**: OLS trend over the last 14 days, extrapolated 24h/48h, with a true 95% *prediction interval* (residual standard error, t-distribution).
- **P(higher in N hours)** = P(forecast price > current price) under that model.
- **Forecast confidence** = how narrow the 48h interval is relative to the price, scaled by sample size (full at 24 readings). No forecast until 6 readings spanning 12+ hours.
- **Recommendation**:
  - **BUY NOW**: departure within 7 days, or (current fare in the cheapest 25% seen or z ≤ −1) and P(higher in 48h) ≥ 55%.
  - **WAIT**: P(higher in 48h) ≤ 40%, more than 14 days to departure, and the fare isn't already cheap.
  - **MONITOR**: everything else, including while collecting data.
- Day-of-week / hour-of-day patterns only after 14 days and 28 readings.

## Free deployment (Render + Neon + GitHub Actions)

1. **Database**: create a free project at [neon.tech](https://neon.tech) and copy the connection string.
2. **Price API**: sign up at [travelpayouts.com](https://www.travelpayouts.com), join the Aviasales program, copy your API token. (Optional: free key at [serpapi.com](https://serpapi.com).)
3. **Render**: New → Blueprint → this repo. It creates `flightnu-api` and `flightnu-web`. On `flightnu-api` set `DATABASE_URL`, `TRAVELPAYOUTS_TOKEN` (and `SERPAPI_KEY`). `CRON_SECRET` and `ADMIN_KEY` are generated for you; copy them from the Environment tab.
   - Upgrading an older deploy: delete the old `flightnu-worker` service and `flightnu-db` database in Render; they are no longer used.
4. **GitHub**: repo Settings → Secrets and variables → Actions → add `FLIGHTNU_API_URL` (`https://flightnu-api.onrender.com`) and `CRON_SECRET`. Then Actions → "Fetch flight prices" → Run workflow once to test.
5. Open the site. Three demo trackers are created on first start (`AUTO_SEED=true`). To delete or pause trackers from the UI, enter `ADMIN_KEY` when prompted.

Free-tier notes: the API sleeps after 15 idle minutes, so the first visit can take ~1 minute (the UI shows a "waking up" message and retries). GitHub pauses scheduled workflows after 60 days without repo activity; re-enable from the Actions tab.

## Local development

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # add TRAVELPAYOUTS_TOKEN (or set PRICE_PROVIDER=simulator)
uvicorn app.main:app --reload --port 8123
python worker.py              # optional: scheduled fetching in another terminal
python -m pytest -q           # tests
```

```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000, uses NEXT_PUBLIC_API_URL (default http://localhost:8123)
```

## API

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/dashboard/summary` | Totals + one card per tracker |
| GET | `/api/trackers` · `/api/trackers/{id}` | Detail returns the latest 1,000 prices and 50 predictions |
| POST | `/api/trackers` | Validates airports (OurAirports list), dates, Discord webhook URL; capped by `MAX_ACTIVE_TRACKERS` |
| POST | `/api/trackers/{id}/refresh` | Fetches a real price now; 10-minute cooldown |
| PATCH / DELETE | `/api/trackers/{id}` | Requires `X-Admin-Key` |
| POST | `/api/internal/ingest` | Requires `X-Cron-Secret`; fetches trackers that are due |
| GET | `/api/status` · `/api/airports?q=` · `/api/health` | |

Airport data: [OurAirports](https://ourairports.com/data/) (public domain).
