from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agent import (
    best_company_from_results,
    detect_intent,
    extract_location,
    extract_request_text,
    tokenize_request_terms,
)
from app.providers import fetch_nearby_places, find_related_website_item, geocode_location

app = FastAPI(title="Closest Company AI Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(Path("static/index.html"))


@app.post("/api/chat")
async def chat(payload: ChatRequest) -> dict:
    message = payload.message.strip()
    intent = detect_intent(message)

    if intent is None:
        return {
            "reply": "I can help find the nearest company. Try asking for coffee, food, medicine, gas, hotel, groceries, or printing services, plus a location.",
            "intent": None,
            "location": None,
            "company": None,
            "website_item": None,
        }

    location_text = extract_location(message)
    request_text = extract_request_text(message)
    request_terms = tokenize_request_terms(request_text)

    try:
        geo = await geocode_location(location_text)
        if geo is None:
            return {
                "reply": f"I understood you need {intent.request_phrase}, but I could not find the location '{location_text}'.",
                "intent": intent.name,
                "location": location_text,
                "company": None,
                "website_item": None,
            }

        lat, lon, resolved_location = geo
        tag_key, tag_value = next(iter(intent.tags.items()))
        nearby = await fetch_nearby_places(lat, lon, tag_key, tag_value)
        best = best_company_from_results(nearby, lat, lon)

        if best is None:
            return {
                "reply": f"I found '{resolved_location}', but no nearby place matched {intent.request_phrase}. Try another nearby area.",
                "intent": intent.name,
                "location": resolved_location,
                "company": None,
                "website_item": None,
            }

        website_item = None
        website_note = ""
        if best.get("website"):
            try:
                website_item = await find_related_website_item(best["website"], request_terms, intent.name)
                if website_item:
                    website_note = (
                        f" I checked {best['name']}'s website and found a related item: "
                        f"{website_item['title']} ({website_item['url']})."
                    )
                else:
                    website_note = " I checked the company website but couldn't confidently match a specific item."
            except httpx.HTTPError:
                website_note = " I found the company website but couldn't access it right now."
        else:
            website_note = " This company did not provide a website in map data."

        reply = (
            f"Best option: {best['name']} is about {best['distance_km']} km away in {resolved_location}. "
            f"Address: {best['address']}.{website_note}"
        )
        return {
            "reply": reply,
            "intent": intent.name,
            "location": resolved_location,
            "company": best,
            "website_item": website_item,
        }

    except httpx.HTTPError:
        return {
            "reply": "I had trouble reaching map services right now. Please try again in a moment.",
            "intent": intent.name,
            "location": location_text,
            "company": None,
            "website_item": None,
        }
