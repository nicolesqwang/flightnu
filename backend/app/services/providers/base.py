from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class ProviderError(Exception):
    """The provider could not be reached or rejected the request."""


@dataclass
class PriceQuote:
    """One real fare: the cheapest offer a provider reports for a route/date."""

    price: float
    airline: str
    source: str
    flight_number: str | None = None
    transfers: int | None = None
    booking_link: str | None = None
    observed_at: datetime | None = None  # set for historical points only


# Common IATA airline designators -> display names. Unknown codes are shown as-is.
AIRLINE_NAMES = {
    "AA": "American", "AC": "Air Canada", "AF": "Air France", "AM": "Aeromexico", "AS": "Alaska",
    "AV": "Avianca", "AY": "Finnair", "AZ": "ITA Airways", "B6": "JetBlue", "BA": "British Airways",
    "BR": "EVA Air", "CI": "China Airlines", "CM": "Copa", "CX": "Cathay Pacific", "DL": "Delta",
    "EI": "Aer Lingus", "EK": "Emirates", "ET": "Ethiopian", "EY": "Etihad", "F9": "Frontier",
    "FI": "Icelandair", "G4": "Allegiant", "HA": "Hawaiian", "IB": "Iberia", "JL": "Japan Airlines",
    "KE": "Korean Air", "KL": "KLM", "LH": "Lufthansa", "LX": "SWISS", "MX": "Breeze",
    "NH": "ANA", "NK": "Spirit", "OS": "Austrian", "OZ": "Asiana", "PR": "Philippine Airlines",
    "QF": "Qantas", "QR": "Qatar Airways", "SK": "SAS", "SQ": "Singapore Airlines", "SY": "Sun Country",
    "TK": "Turkish Airlines", "TP": "TAP Air Portugal", "UA": "United", "VS": "Virgin Atlantic",
    "WN": "Southwest", "WS": "WestJet", "Y4": "Volaris", "VB": "Viva Aerobus", "FR": "Ryanair",
    "U2": "easyJet", "W6": "Wizz Air", "VY": "Vueling", "NZ": "Air New Zealand", "MU": "China Eastern",
    "CA": "Air China", "CZ": "China Southern", "AI": "Air India", "VN": "Vietnam Airlines",
    "LA": "LATAM", "G3": "GOL", "AD": "Azul", "SA": "South African", "MS": "EgyptAir",
}


def airline_name(code: str | None) -> str:
    if not code:
        return "Unknown"
    return AIRLINE_NAMES.get(code.upper(), code.upper())
