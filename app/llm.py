from __future__ import annotations

import os
from typing import Any

import httpx

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


def openai_key_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _build_prompt(user_message: str, intent: str, location: str, company: dict[str, Any], website_item: dict[str, Any] | None) -> str:
    return (
        "You are an ordering concierge assistant. Use the supplied structured data and write a short helpful answer. "
        "Include: best company, distance, address, and if available the best website item. "
        "Keep it under 90 words and action-oriented.\n\n"
        f"User request: {user_message}\n"
        f"Intent: {intent}\n"
        f"Location: {location}\n"
        f"Company: {company.get('name')} | distance_km={company.get('distance_km')} | address={company.get('address')}\n"
        f"Company website: {company.get('website')}\n"
        f"Website item: {website_item}\n"
    )


def _extract_text(payload: dict[str, Any]) -> str | None:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    for item in payload.get("output", []):
        for content in item.get("content", []):
            maybe_text = content.get("text")
            if isinstance(maybe_text, str) and maybe_text.strip():
                return maybe_text.strip()
    return None


async def generate_chatgpt_reply(
    *,
    user_message: str,
    intent: str,
    location: str,
    company: dict[str, Any],
    website_item: dict[str, Any] | None,
) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    prompt = _build_prompt(user_message, intent, location, company, website_item)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "gpt-4.1-mini",
        "input": prompt,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(OPENAI_RESPONSES_URL, json=body, headers=headers)
        response.raise_for_status()
        payload = response.json()

    return _extract_text(payload)
