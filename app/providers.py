from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_anchor = False
        self._current_href = ""
        self._buffer: list[str] = []
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._in_anchor = True
        attr_map = {k: v or "" for k, v in attrs}
        self._current_href = attr_map.get("href", "")
        self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._in_anchor:
            return
        text = " ".join(part.strip() for part in self._buffer if part.strip()).strip()
        if self._current_href:
            self.links.append({"href": self._current_href, "text": text})
        self._in_anchor = False
        self._current_href = ""
        self._buffer = []


async def geocode_location(query: str) -> tuple[float, float, str] | None:
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": "closest-company-ai-agent/1.0"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()

    if not payload:
        return None

    top = payload[0]
    return float(top["lat"]), float(top["lon"]), top.get("display_name", query)


async def fetch_nearby_places(lat: float, lon: float, tag_key: str, tag_value: str, radius_m: int = 7000) -> list[dict]:
    query = f"""
    [out:json][timeout:25];
    (
      node[\"{tag_key}\"=\"{tag_value}\"](around:{radius_m},{lat},{lon});
      way[\"{tag_key}\"=\"{tag_value}\"](around:{radius_m},{lat},{lon});
      relation[\"{tag_key}\"=\"{tag_value}\"](around:{radius_m},{lat},{lon});
    );
    out center tags;
    """
    headers = {"User-Agent": "closest-company-ai-agent/1.0"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(OVERPASS_URL, data=query, headers=headers)
        response.raise_for_status()
        payload = response.json()

    return payload.get("elements", [])


def _normalize_website_url(url: str) -> str:
    clean = url.strip()
    if clean.startswith("http://") or clean.startswith("https://"):
        return clean
    return f"https://{clean}"


def _score_link(text: str, href: str, request_terms: list[str], intent_name: str) -> int:
    haystack = f"{text} {href}".lower()
    score = 0
    if intent_name and intent_name in haystack:
        score += 2
    for term in request_terms:
        if term in haystack:
            score += 3
    return score


async def find_related_website_item(website_url: str, request_terms: list[str], intent_name: str) -> dict | None:
    normalized = _normalize_website_url(website_url)
    headers = {"User-Agent": "closest-company-ai-agent/1.0"}

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(normalized, headers=headers)
        response.raise_for_status()
        html = response.text

    parser = LinkParser()
    parser.feed(html)

    best: dict | None = None
    best_score = 0

    for link in parser.links:
        text = link["text"] or "Untitled link"
        href = link["href"]
        score = _score_link(text, href, request_terms, intent_name)
        if score > best_score:
            best_score = score
            best = {
                "title": text,
                "url": urljoin(normalized, href),
                "match_score": score,
            }

    return best if best_score > 0 else None
