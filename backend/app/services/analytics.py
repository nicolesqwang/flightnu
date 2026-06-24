"""Statistical analytics engine: moving averages, anomaly detection,
linear regression forecasting, and buy/wait/monitor recommendations."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from app.models.models import PriceObservation, Recommendation

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass
class AnalyticsResult:
    current_price: float
    historical_average: float
    historical_low: float
    historical_high: float
    std_dev: float
    z_score: float
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
    cheapest_day_of_week: str | None = None
    most_expensive_day_of_week: str | None = None
    cheapest_hour_of_day: int | None = None
    most_expensive_hour_of_day: int | None = None
    volatility_score: float = 0.0
    series: list[dict] = field(default_factory=list)


def simple_moving_average(prices: np.ndarray, window: int = 5) -> np.ndarray:
    if len(prices) == 0:
        return np.array([])
    window = max(1, min(window, len(prices)))
    cumsum = np.cumsum(np.insert(prices, 0, 0))
    sma = (cumsum[window:] - cumsum[:-window]) / window
    pad = np.full(window - 1, sma[0] if len(sma) else prices[0])
    return np.concatenate([pad, sma]) if len(sma) else prices.copy()


def ewma(prices: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    if len(prices) == 0:
        return np.array([])
    out = np.empty_like(prices, dtype=float)
    out[0] = prices[0]
    for i in range(1, len(prices)):
        out[i] = alpha * prices[i] + (1 - alpha) * out[i - 1]
    return out


def z_score(value: float, mean: float, std: float) -> float:
    if std == 0:
        return 0.0
    return (value - mean) / std


def linear_regression_forecast(
    timestamps: np.ndarray, prices: np.ndarray, hours_ahead: float
) -> tuple[float, float, float]:
    """Returns (predicted_value, slope_per_hour, residual_std)."""
    n = len(prices)
    if n < 2:
        return float(prices[-1]) if n else 0.0, 0.0, 0.0

    t0 = timestamps[0]
    x = np.array([(t - t0) / 3600.0 for t in timestamps])  # hours since first obs
    slope, intercept = np.polyfit(x, prices, 1)

    predicted_y = slope * x + intercept
    residuals = prices - predicted_y
    residual_std = float(np.std(residuals)) if n > 2 else float(np.std(prices))

    x_future = x[-1] + hours_ahead
    forecast = slope * x_future + intercept
    return float(forecast), float(slope), residual_std


def _prob_price_increase(slope: float, residual_std: float, current_price: float) -> float:
    """Probability that price increases, modeled via a normal distribution
    centered on the regression trend (z of 0 threshold)."""
    if residual_std <= 0:
        return 1.0 if slope > 0 else (0.0 if slope < 0 else 0.5)
    z = slope / (residual_std / max(1.0, math.sqrt(2)))
    return float(_norm_cdf(z))


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def compute_seasonality(observations: list[PriceObservation]) -> dict:
    by_day: dict[str, list[float]] = defaultdict(list)
    by_hour: dict[int, list[float]] = defaultdict(list)
    for obs in observations:
        by_day[DAY_NAMES[obs.timestamp.weekday()]].append(obs.price)
        by_hour[obs.timestamp.hour].append(obs.price)

    cheapest_day = min(by_day, key=lambda d: np.mean(by_day[d])) if by_day else None
    priciest_day = max(by_day, key=lambda d: np.mean(by_day[d])) if by_day else None
    cheapest_hour = min(by_hour, key=lambda h: np.mean(by_hour[h])) if by_hour else None
    priciest_hour = max(by_hour, key=lambda h: np.mean(by_hour[h])) if by_hour else None

    return {
        "cheapest_day_of_week": cheapest_day,
        "most_expensive_day_of_week": priciest_day,
        "cheapest_hour_of_day": cheapest_hour,
        "most_expensive_hour_of_day": priciest_hour,
    }


def build_explanation(
    current_price: float,
    historical_average: float,
    pct_below_avg: float,
    percentile: float,
    recommendation: Recommendation,
    prob_increase_48h: float,
    expected_increase: float,
    confidence_score: float,
) -> str:
    direction = "below" if pct_below_avg > 0 else "above"
    pct_abs = abs(pct_below_avg)

    if recommendation == Recommendation.BUY_NOW:
        return (
            f"Current price is {pct_abs:.0f}% {direction} historical average and falls within the "
            f"bottom {percentile:.1f}% of observed prices. Model predicts a {prob_increase_48h * 100:.0f}% "
            f"probability that prices will increase by more than ${abs(expected_increase):.0f} within the "
            f"next 48 hours. Confidence: {confidence_score:.0f}%."
        )
    if recommendation == Recommendation.WAIT:
        return (
            f"Current price is {pct_abs:.0f}% {direction} historical average. Model confidence is "
            f"{confidence_score:.0f}% and the trend points toward lower prices ahead, so waiting is "
            f"likely to yield a better fare."
        )
    return (
        f"Current price is {pct_abs:.0f}% {direction} historical average with no strong signal in either "
        f"direction (confidence {confidence_score:.0f}%). Continue monitoring for a clearer entry point."
    )


def run_analytics(observations: list[PriceObservation]) -> AnalyticsResult | None:
    if not observations:
        return None

    observations = sorted(observations, key=lambda o: o.timestamp)
    prices = np.array([o.price for o in observations], dtype=float)
    timestamps = np.array([o.timestamp.timestamp() for o in observations], dtype=float)

    current_price = float(prices[-1])
    historical_average = float(np.mean(prices))
    historical_low = float(np.min(prices))
    historical_high = float(np.max(prices))
    std = float(np.std(prices))

    sma_series = simple_moving_average(prices, window=5)
    ewma_series = ewma(prices, alpha=0.3)
    sma_latest = float(sma_series[-1])
    ewma_latest = float(ewma_series[-1])

    z = z_score(current_price, historical_average, std)
    percentile = float((prices <= current_price).mean() * 100)

    forecast_24h, slope, residual_std = linear_regression_forecast(timestamps, prices, hours_ahead=24)
    forecast_48h, _, _ = linear_regression_forecast(timestamps, prices, hours_ahead=48)

    prob_increase_24h = _prob_price_increase(slope, residual_std, current_price)
    prob_increase_48h = _prob_price_increase(slope * 1.2, residual_std, current_price)

    expected_increase = max(0.0, forecast_48h - current_price)
    expected_decrease = max(0.0, current_price - forecast_48h)

    margin = 1.96 * (residual_std if residual_std > 0 else std)
    ci_low = forecast_48h - margin
    ci_high = forecast_48h + margin

    n = len(prices)
    sample_size_factor = min(1.0, n / 30.0)
    fit_quality = 1.0 - min(1.0, (residual_std / historical_average) if historical_average else 0)
    confidence_score = float(max(0.0, min(100.0, (0.6 * sample_size_factor + 0.4 * fit_quality) * 100)))

    volatility_score = float((std / historical_average) * 100) if historical_average else 0.0

    recommendation = _recommend(z, confidence_score, forecast_48h, current_price)

    pct_below_avg = ((historical_average - current_price) / historical_average * 100) if historical_average else 0.0

    explanation = build_explanation(
        current_price=current_price,
        historical_average=historical_average,
        pct_below_avg=pct_below_avg,
        percentile=percentile,
        recommendation=recommendation,
        prob_increase_48h=prob_increase_48h,
        expected_increase=expected_increase,
        confidence_score=confidence_score,
    )

    seasonality = compute_seasonality(observations)

    series = [
        {
            "timestamp": obs.timestamp.isoformat(),
            "price": obs.price,
            "sma": float(sma_series[i]),
            "ewma": float(ewma_series[i]),
        }
        for i, obs in enumerate(observations)
    ]

    return AnalyticsResult(
        current_price=current_price,
        historical_average=historical_average,
        historical_low=historical_low,
        historical_high=historical_high,
        std_dev=std,
        z_score=z,
        sma=sma_latest,
        ewma=ewma_latest,
        predicted_price_24h=forecast_24h,
        predicted_price_48h=forecast_48h,
        prob_increase_24h=prob_increase_24h,
        prob_increase_48h=prob_increase_48h,
        expected_increase=expected_increase,
        expected_decrease=expected_decrease,
        confidence_interval_low=ci_low,
        confidence_interval_high=ci_high,
        confidence_score=confidence_score,
        recommendation=recommendation,
        explanation=explanation,
        volatility_score=volatility_score,
        series=series,
        **seasonality,
    )


def _recommend(
    z: float, confidence_score: float, predicted_price_48h: float, current_price: float
) -> Recommendation:
    if z < -2 and confidence_score > 80 and predicted_price_48h > current_price:
        return Recommendation.BUY_NOW
    if confidence_score < 60 or predicted_price_48h < current_price:
        return Recommendation.WAIT
    return Recommendation.MONITOR
