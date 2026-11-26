import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.models.models import Recommendation
from app.services.analytics import MIN_FORECAST_OBS, run_analytics

NOW = datetime(2026, 11, 25, 12, 0)
FAR = date(2027, 2, 1)  # 68 days out


@dataclass
class Obs:
    price: float
    timestamp: datetime


def series(prices, step_hours=4):
    start = NOW - timedelta(hours=step_hours * (len(prices) - 1))
    return [Obs(p, start + timedelta(hours=step_hours * i)) for i, p in enumerate(prices)]


def test_collecting_until_enough_data():
    r = run_analytics(series([300, 305, 298]), FAR, NOW)
    assert r.has_forecast is False
    assert r.recommendation == Recommendation.MONITOR
    assert r.confidence_score == 0
    assert f"3 of {MIN_FORECAST_OBS}" in r.explanation


def test_final_week_buys():
    r = run_analytics(series([300, 310]), NOW.date() + timedelta(days=5), NOW)
    assert r.recommendation == Recommendation.BUY_NOW


def test_cheap_dip_in_rising_market_is_buy():
    rng = random.Random(1)
    prices = [250 + 2.5 * i + rng.gauss(0, 3) for i in range(30)]
    prices[-1] = min(prices) - 5  # today's fare is the cheapest seen
    r = run_analytics(series(prices), FAR, NOW)
    assert r.has_forecast
    assert r.percentile == 0
    assert r.prob_increase_48h > 0.55
    assert r.recommendation == Recommendation.BUY_NOW
    assert "Good price" in r.explanation


def test_falling_market_is_wait():
    rng = random.Random(2)
    prices = [400 - 3 * i + rng.gauss(0, 3) for i in range(30)]
    r = run_analytics(series(prices), FAR, NOW)
    assert r.prob_increase_48h < 0.4
    assert r.predicted_price_48h < r.current_price
    assert r.recommendation in (Recommendation.WAIT, Recommendation.MONITOR)


def test_probability_and_confidence_respond_to_data():
    rng = random.Random(3)
    calm = run_analytics(series([300 + rng.gauss(0, 2) for _ in range(30)]), FAR, NOW)
    noisy = run_analytics(series([300 + rng.gauss(0, 60) for _ in range(30)]), FAR, NOW)
    assert calm.confidence_score > noisy.confidence_score + 20
    rising = run_analytics(series([300 + 4 * i for i in range(30)]), FAR, NOW)
    assert rising.prob_increase_48h > 0.9


def test_prediction_interval_contains_forecast():
    rng = random.Random(4)
    r = run_analytics(series([300 + rng.gauss(0, 10) for _ in range(20)]), FAR, NOW)
    assert r.confidence_interval_low < r.predicted_price_48h < r.confidence_interval_high


def test_seasonality_needs_two_weeks():
    short = run_analytics(series([300 + i for i in range(40)], step_hours=4), FAR, NOW)  # ~6.5 days
    assert short.cheapest_day_of_week is None
    long = run_analytics(series([300 + (i % 7) for i in range(120)], step_hours=4), FAR, NOW)  # 20 days
    assert long.cheapest_day_of_week is not None
