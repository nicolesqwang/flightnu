"""Outbound alert delivery: Discord webhook + email."""

from __future__ import annotations

import logging
import re
import smtplib
from email.mime.text import MIMEText

import httpx

from app.core.config import get_settings
from app.models.models import Prediction, Tracker

logger = logging.getLogger("flightnu.alerts")

# Only real Discord webhook URLs, so the server can't be used to POST anywhere.
DISCORD_WEBHOOK_RE = re.compile(
    r"^https://(?:(?:canary|ptb)\.)?(?:discord|discordapp)\.com/api/webhooks/\d+/[A-Za-z0-9_\-]+$"
)


def is_valid_discord_webhook(url: str) -> bool:
    return bool(DISCORD_WEBHOOK_RE.match(url.strip()))


def format_alert_text(tracker: Tracker, prediction: Prediction) -> str:
    lines = [
        "FLIGHTNU BUY ALERT",
        f"Route: {tracker.origin_airport} → {tracker.destination_airport}, departing {tracker.departure_date:%b %d, %Y}",
        f"Current price: ${prediction.current_price:,.0f} (average ${prediction.historical_average:,.0f})",
        f"Confidence: {prediction.confidence_score:.0f}%",
        "",
        prediction.explanation,
    ]
    return "\n".join(lines)


def send_discord_alert(webhook_url: str, tracker: Tracker, prediction: Prediction) -> bool:
    if not is_valid_discord_webhook(webhook_url):
        logger.warning("Refusing non-Discord webhook URL for tracker %s", tracker.id)
        return False
    try:
        resp = httpx.post(webhook_url, json={"content": format_alert_text(tracker, prediction)}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception:
        logger.exception("Failed to send Discord alert for tracker %s", tracker.id)
        return False


def send_email_alert(to_email: str, tracker: Tracker, prediction: Prediction) -> bool:
    settings = get_settings()
    if not settings.smtp_host:
        logger.info("SMTP not configured; skipping email alert for tracker %s", tracker.id)
        return False
    try:
        msg = MIMEText(format_alert_text(tracker, prediction))
        msg["Subject"] = f"FlightNu: buy {tracker.origin_airport} → {tracker.destination_airport} at ${prediction.current_price:,.0f}"
        msg["From"] = settings.alert_from_email or settings.smtp_username or "alerts@flightnu.app"
        msg["To"] = to_email
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email alert for tracker %s", tracker.id)
        return False


def dispatch_alerts(tracker: Tracker, prediction: Prediction) -> bool:
    """Returns True if at least one alert was delivered."""
    if not tracker.alerts_enabled or prediction.recommendation.value != "BUY_NOW":
        return False
    settings = get_settings()
    sent = False
    webhook = tracker.discord_webhook_url or settings.discord_webhook_url
    if webhook:
        sent = send_discord_alert(webhook, tracker, prediction) or sent
    if tracker.alert_email:
        sent = send_email_alert(tracker.alert_email, tracker, prediction) or sent
    return sent
