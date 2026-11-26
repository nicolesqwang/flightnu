"""Statistical analytics engine for one tracker's price history.

What each number means (shown to users, so it must be honest):

* historical_* / std_dev / z_score: descriptive stats over every observation.
* percentile: % of observed prices that were cheaper than the current price
  (0 = cheapest ever seen, 100 = most expensive).
* Forecasts: ordinary least-squares trend over the recent window (last 14
  days), extrapolated 24h / 48h. The 95% interval is a proper *prediction*
  interval (residual standard error, t-distribution, distance from the mean
  of x), not just +/- 2 standard deviations.
* prob_increase_Nh: P(price in N hours > current price) under that model.
* confidence_score: how tight the 48h prediction interval is relative to the
  price, scaled down while there is little data. Wide interval -> low score.
* No forecast is made until there are MIN_FORECAST_OBS observations spanning
  at least MIN_FORECAST_SPAN_HOURS; until then the tracker is "collecting data".
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Protocol, Sequence

import numpy as np

from app.models.models import Recommendation

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

MIN_FORECAST_OBS = 6
MIN_FORECAST_SPAN_HOURS = 12
REGRESSION_WINDOW_DAYS = 14
FULL_CONFIDENCE_OBS = 24
SEASONALITY_MIN_DAYS = 14
SEASONALITY_MIN_OBS = 28

# Recommendation thresholds (documented in the README and shown in explanations).
BUY_PERCENTILE = 25.0
BUY_Z = -1.0
BUY_PROB_UP = 0.55
WAIT_PROB_UP = 0.40
WAIT_MIN_DAYS = 14
FINAL_WEEK_DAYS = 7

# Two-sided 95% t critical values by degrees of freedom.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
        10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}


def t_critical(df: int) -> float:
    if df <= 0:
        return float("inf")
    for k in sorted(_T95):
        if df <= k:
            return _T95[k]
    return 1.96


class Observation(Protocol):
    price: float
    timestamp: datetime


@dataclass
class AnalyticsResult:
    current_price: float
    historical_average: float
    historical_low: float
    historical_high: float
    std_dev: float
    z_score: float
    percentile: float
    sma: float
    ewma: float
    predicted_price_24h: float
    predicted_price_48h: float
    prob_increase_24h: float
    prob_increase_48h: float
    expected_increase: float
    expected_decrease: float
    confidence_interval_low: float
    confidence_interval_high: float
    confidence_score: float
    recommendation: Recommendation
    explanation: str
    observation_count: int
    days_to_departure: int
    has_forecast: bool
    cheapest_day_of_week: str | None = None
    most_expensive_day_of_week: str | None = None
    cheapest_hour_of_day: int | None = None
    most_expensive_hour_of_day: int | None = None
    volatility_score: float = 0.0
    series: list[dict] = field(default_factory=list)


def simple_moving_average(prices: np.ndarray, window: int = 5) -> np.ndarray:
    """Trailing mean; early points average whatever history exists."""
    out = np.empty(len(prices), dtype=float)
    for i in range(len(prices)):
        out[i] = prices[max(0, i - window + 1): i + 1].mean()
    return out


def ewma(prices: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    if len(prices) == 0:
        return np.array([])
    out = np.empty_like(prices, dtype=float)
    out[0] = prices[0]
    for i in range(1, len(prices)):
        out[i] = alpha * prices[i] + (1 - alpha) * out[i - 1]
    return out


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


@dataclass
class Forecast:
    value_24h: float
    value_48h: float
    se_24h: float
    se_48h: float
    t: float
    slope_per_day: float


def trend_forecast(hours: np.ndarray, prices: np.ndarray) -> Forecast | None:
    """OLS fit price ~ a + b*hours with prediction standard errors."""
    n = len(prices)
    if n < MIN_FORECAST_OBS or hours[-1] - hours[0] < MIN_FORECAST_SPAN_HOURS:
        return None
    x_bar = hours.mean()
    sxx = float(((hours - x_bar) ** 2).sum())
    if sxx == 0:
        return None
    slope, intercept = np.polyfit(hours, prices, 1)
    residuals = prices - (slope * hours + intercept)
    s = math.sqrt(float((residuals ** 2).sum()) / (n - 2))

    def at(h_ahead: float) -> tuple[float, float]:
        x0 = hours[-1] + h_ahead
        yhat = float(slope * x0 + intercept)
        se = s * math.sqrt(1 + 1 / n + (x0 - x_bar) ** 2 / sxx)
        return max(yhat, 1.0), se

    v24, se24 = at(24)
    v48, se48 = at(48)
    return Forecast(v24, v48, se24, se48, t_critical(n - 2), float(slope) * 24)


def _prob_above(current: float, forecast: float, se: float) -> float:
    if se <= 0:
        return 1.0 if forecast > current else (0.0 if forecast < current else 0.5)
    return 1 - _norm_cdf((current - forecast) / se)


def compute_seasonality(observations: Sequence[Observation]) -> dict:
    empty = {
        "cheapest_day_of_week": None,
        "most_expensive_day_of_week": None,
        "cheapest_hour_of_day": None,
        "most_expensive_hour_of_day": None,
    }
    if len(observations) < SEASONALITY_MIN_OBS:
        return empty
    span = observations[-1].timestamp - observations[0].timestamp
    if span < timedelta(days=SEASONALITY_MIN_DAYS):
        return empty
    by_day: dict[str, list[float]] = defaultdict(list)
    by_hour: dict[int, list[float]] = defaultdict(list)
    for obs in observations:
        by_day[DAY_NAMES[obs.timestamp.weekday()]].append(obs.price)
        by_hour[obs.timestamp.hour].append(obs.price)
    return {
        "cheapest_day_of_week": min(by_day, key=lambda d: np.mean(by_day[d])),
        "most_expensive_day_of_week": max(by_day, key=lambda d: np.mean(by_day[d])),
        "cheapest_hour_of_day": min(by_hour, key=lambda h: np.mean(by_hour[h])),
        "most_expensive_hour_of_day": max(by_hour, key=lambda h: np.mean(by_hour[h])),
    }


def _recommend(
    *,
    has_forecast: bool,
    days_out: int,
    percentile: float,
    z: float,
    prob_up_48h: float,
) -> tuple[Recommendation, str]:
    """Returns (recommendation, reason_code)."""
    if days_out <= FINAL_WEEK_DAYS:
        return Recommendation.BUY_NOW, "final_week"
    if not has_forecast:
        return Recommendation.MONITOR, "collecting"
    cheap = percentile <= BUY_PERCENTILE or z <= BUY_Z
    if cheap and prob_up_48h >= BUY_PROB_UP:
        return Recommendation.BUY_NOW, "cheap_and_rising"
    if prob_up_48h <= WAIT_PROB_UP and days_out > WAIT_MIN_DAYS and not cheap:
        return Recommendation.WAIT, "falling"
    if cheap:
        return Recommendation.MONITOR, "cheap_but_falling"
    return Recommendation.MONITOR, "no_signal"


def build_explanation(
    reason: str,
    *,
    current: float,
    average: float,
    percentile: float,
    n: int,
    days_out: int,
    forecast_48h: float,
    prob_up_48h: float,
    ci: tuple[float, float],
) -> str:
    diff_pct = (current - average) / average * 100 if average else 0.0
    if abs(diff_pct) < 1:
        rel = f"in line with its average of ${average:,.0f}"
    else:
        rel = f"{abs(diff_pct):.0f}% {'below' if diff_pct < 0 else 'above'} its average of ${average:,.0f}"
    seen = f"${current:,.0f} is {rel} across {n} observations"
    cheaper_than = f"cheaper than {100 - percentile:.0f}% of prices seen"
    fc = (
        f"The trend model projects ${forecast_48h:,.0f} in 48 hours "
        f"(95% range ${ci[0]:,.0f}–${ci[1]:,.0f}), a {prob_up_48h * 100:.0f}% chance the fare is higher then"
    )
    if reason == "final_week":
        return (
            f"Departure is {days_out} day{'s' if days_out != 1 else ''} away. Fares rarely fall in the final week, "
            f"so book now. Current fare {seen}."
        )
    if reason == "collecting":
        return (
            f"Collecting data: {n} of {MIN_FORECAST_OBS} observations needed (spanning {MIN_FORECAST_SPAN_HOURS}+ hours) "
            f"before forecasting. Current fare: ${current:,.0f}."
        )
    if reason == "cheap_and_rising":
        return f"Good price: {seen}, {cheaper_than}. {fc}. Buying now locks in the lower fare."
    if reason == "falling":
        return f"Prices are trending down: {seen}. {fc}. With {days_out} days to departure, waiting is reasonable."
    if reason == "cheap_but_falling":
        return f"Already a low fare ({cheaper_than}), but the trend still points down. {fc}. Watch for the next reading."
    return f"No strong signal: {seen}. {fc}. Keep monitoring."


def run_analytics(
    observations: Sequence[Observation], departure_date: date, now: datetime
) -> AnalyticsResult | None:
    if not observations:
        return None

    observations = sorted(observations, key=lambda o: o.timestamp)
    prices = np.array([o.price for o in observations], dtype=float)
    n = len(prices)

    current = float(prices[-1])
    average = float(prices.mean())
    low, high = float(prices.min()), float(prices.max())
    std = float(prices.std(ddof=1)) if n > 1 else 0.0
    z = (current - average) / std if std > 0 else 0.0
    percentile = float((prices < current).mean() * 100)
    days_out = (departure_date - now.date()).days

    sma_series = simple_moving_average(prices, 5)
    ewma_series = ewma(prices, 0.3)

    window_start = observations[-1].timestamp - timedelta(days=REGRESSION_WINDOW_DAYS)
    recent = [o for o in observations if o.timestamp >= window_start]
    if len(recent) < MIN_FORECAST_OBS:
        recent = list(observations)
    t0 = recent[0].timestamp
    hours = np.array([(o.timestamp - t0).total_seconds() / 3600 for o in recent], dtype=float)
    fc = trend_forecast(hours, np.array([o.price for o in recent], dtype=float))

    if fc:
        f24, f48 = fc.value_24h, fc.value_48h
        half = fc.t * fc.se_48h
        ci = (max(0.0, f48 - half), f48 + half)
        p24 = _prob_above(current, f24, fc.se_24h)
        p48 = _prob_above(current, f48, fc.se_48h)
        sample_factor = min(1.0, n / FULL_CONFIDENCE_OBS)
        precision = max(0.0, 1 - half / current) if current else 0.0
        confidence = round(100 * sample_factor * precision, 1)
    else:
        f24 = f48 = current
        ci = (current, current)
        p24 = p48 = 0.5
        confidence = 0.0

    rec, reason = _recommend(has_forecast=fc is not None, days_out=days_out, percentile=percentile, z=z, prob_up_48h=p48)
    explanation = build_explanation(
        reason,
        current=current,
        average=average,
        percentile=percentile,
        n=n,
        days_out=days_out,
        forecast_48h=f48,
        prob_up_48h=p48,
        ci=ci,
    )

    series = [
        {"timestamp": o.timestamp.isoformat(), "price": o.price, "sma": float(sma_series[i]), "ewma": float(ewma_series[i])}
        for i, o in enumerate(observations)
    ]

    return AnalyticsResult(
        current_price=current,
        historical_average=average,
        historical_low=low,
        historical_high=high,
        std_dev=std,
        z_score=z,
        percentile=percentile,
        sma=float(sma_series[-1]),
        ewma=float(ewma_series[-1]),
        predicted_price_24h=f24,
        predicted_price_48h=f48,
        prob_increase_24h=p24,
        prob_increase_48h=p48,
        expected_increase=max(0.0, f48 - current),
        expected_decrease=max(0.0, current - f48),
        confidence_interval_low=ci[0],
        confidence_interval_high=ci[1],
        confidence_score=confidence,
        recommendation=rec,
        explanation=explanation,
        observation_count=n,
        days_to_departure=days_out,
        has_forecast=fc is not None,
        volatility_score=(std / average * 100) if average else 0.0,
        series=series,
        **compute_seasonality(observations),
    )
