from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any


@dataclass(frozen=True)
class IntentDefinition:
    name: str
    keywords: tuple[str, ...]
    tags: dict[str, str]
    request_phrase: str


INTENTS: tuple[IntentDefinition, ...] = (
    IntentDefinition(
        name="pharmacy",
        keywords=("medicine", "drug", "pharmacy", "prescription", "painkiller"),
        tags={"amenity": "pharmacy"},
        request_phrase="medicine or pharmacy services",
    ),
    IntentDefinition(
        name="food",
        keywords=("food", "eat", "restaurant", "meal", "lunch", "dinner"),
        tags={"amenity": "restaurant"},
        request_phrase="a meal",
    ),
    IntentDefinition(
        name="coffee",
        keywords=("coffee", "cafe", "latte", "espresso"),
        tags={"amenity": "cafe"},
        request_phrase="coffee",
    ),
    IntentDefinition(
        name="grocery",
        keywords=("grocery", "supermarket", "groceries", "food shopping"),
        tags={"shop": "supermarket"},
        request_phrase="groceries",
    ),
    IntentDefinition(
        name="gas",
        keywords=("gas", "fuel", "petrol", "station"),
        tags={"amenity": "fuel"},
        request_phrase="fuel",
    ),
    IntentDefinition(
        name="hotel",
        keywords=("hotel", "stay", "accommodation", "room"),
        tags={"tourism": "hotel"},
        request_phrase="a place to stay",
    ),
    IntentDefinition(
        name="printing",
        keywords=("print", "printing", "documents", "copy", "photocopy"),
        tags={"shop": "copyshop"},
        request_phrase="printing services",
    ),
)


def detect_intent(message: str) -> IntentDefinition | None:
    lowered = message.lower().strip()
    if not lowered:
        return None

    for intent in INTENTS:
        if any(keyword in lowered for keyword in intent.keywords):
            return intent
    return None


def extract_location(message: str) -> str:
    lowered = message.lower().strip()
    separators = (" near ", " in ", " around ", " at ")
    for separator in separators:
        idx = lowered.find(separator)
        if idx != -1:
            raw = message[idx + len(separator) :].strip()
            return raw.title() if raw else "Current location"
    return "Current location"


def extract_request_text(message: str) -> str:
    lowered = message.lower()
    separators = (" near ", " in ", " around ", " at ")
    cut = len(message)
    for separator in separators:
        idx = lowered.find(separator)
        if idx != -1:
            cut = min(cut, idx)
    request = message[:cut].strip(" .,")
    return request or "request"


def tokenize_request_terms(text: str) -> list[str]:
    clean = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in text)
    stop_words = {
        "i",
        "need",
        "want",
        "find",
        "me",
        "to",
        "the",
        "a",
        "an",
        "for",
        "please",
        "my",
        "get",
        "buy",
        "order",
    }
    return [token for token in clean.split() if len(token) > 2 and token not in stop_words]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius_km * c


def best_company_from_results(items: list[dict[str, Any]], origin_lat: float, origin_lon: float) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for item in items:
        tags = item.get("tags", {})
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is None or lon is None:
            center = item.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
        if lat is None or lon is None:
            continue

        distance_km = haversine_km(origin_lat, origin_lon, float(lat), float(lon))
        address = tags.get("addr:full") or ", ".join(
            filter(
                None,
                [
                    tags.get("addr:housenumber"),
                    tags.get("addr:street"),
                    tags.get("addr:city"),
                ],
            )
        )
        website = tags.get("website") or tags.get("contact:website") or tags.get("url")

        company = {
            "name": tags.get("name", "Unnamed business"),
            "distance_km": round(distance_km, 2),
            "address": address or "Address unavailable",
            "lat": float(lat),
            "lon": float(lon),
            "website": website,
        }

        if best is None or company["distance_km"] < best["distance_km"]:
            best = company

    return best
