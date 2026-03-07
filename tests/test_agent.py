from app.agent import (
    best_company_from_results,
    detect_intent,
    extract_location,
    extract_request_text,
    haversine_km,
    tokenize_request_terms,
)

def test_detect_intent_coffee() -> None:
    intent = detect_intent("I need coffee near Miami")
    assert intent is not None
    assert intent.name == "coffee"


def test_extract_location_from_text() -> None:
    assert extract_location("Find medicine in Nairobi") == "Nairobi"


def test_extract_request_text() -> None:
    assert extract_request_text("Need iced coffee near Austin") == "Need iced coffee"


def test_tokenize_request_terms() -> None:
    assert tokenize_request_terms("I need iced coffee with milk") == ["iced", "coffee", "with", "milk"]


def test_haversine_zero_distance() -> None:
    assert haversine_km(40.0, -70.0, 40.0, -70.0) == 0


def test_best_company_chooses_closest_and_website() -> None:
    items = [
        {"lat": 40.01, "lon": -70.0, "tags": {"name": "Far One", "website": "https://far.example"}},
        {"lat": 40.0005, "lon": -70.0, "tags": {"name": "Near One", "website": "near.example"}},
    ]
    best = best_company_from_results(items, 40.0, -70.0)
    assert best is not None
    assert best["name"] == "Near One"
    assert best["website"] == "near.example"

