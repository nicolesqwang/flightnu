"""Outbound alert delivery: Discord webhook + email."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

import httpx

from app.core.config import get_settings
from app.models.models import Prediction, Tracker

logger = logging.getLogger("flightnu.alerts")


def format_alert_text(tracker: Tracker, prediction: Prediction) -> str:
    return (
        "🚨 FLIGHTNU ALERT\n\n"
        f"Route:\n{tracker.origin_airport} → {tracker.destination_airport}\n\n"
        f"Current Price:\n${prediction.current_price:.0f}\n\n"
        f"Historical Average:\n${prediction.historical_average:.0f}\n\n"
        f"Z-Score:\n{prediction.z_score:.1f}\n\n"
        f"Prediction Confidence:\n{prediction.confidence_score:.0f}%\n\n"
        f"Expected Increase:\n+${prediction.expected_increase:.0f} within 48 hours\n\n"
        f"Recommendation:\n{prediction.recommendation.value.replace('_', ' ')}"
    )


def send_discord_alert(webhook_url: str, tracker: Tracker, prediction: Prediction) -> bool:
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
        msg["Subject"] = f"FlightNu Alert: {tracker.origin_airport} -> {tracker.destination_airport}"
        msg["From"] = settings.alert_from_email or settings.smtp_username or "alerts@flightnu.app"
        msg["To"] = to_email

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email alert for tracker %s", tracker.id)
        return False


def dispatch_alerts(tracker: Tracker, prediction: Prediction) -> None:
    if not tracker.alerts_enabled:
        return
    if prediction.recommendation.value != "BUY_NOW":
        return

    settings = get_settings()
    webhook = tracker.discord_webhook_url or settings.discord_webhook_url
    if webhook:
        send_discord_alert(webhook, tracker, prediction)
    if tracker.alert_email:
        send_email_alert(tracker.alert_email, tracker, prediction)
