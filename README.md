# Closest Company AI Agent

A full-stack AI-style assistant you can text to find the nearest company where you can request something and get it.

## What it does

- Chat-style interface (web app) with an order builder side panel and quick categories
- Understands a request like:
  - "I need pain medicine near Brooklyn"
  - "Where can I print documents in San Francisco?"
- Detects intent (what you want)
- Geocodes location using OpenStreetMap Nominatim
- Searches nearby businesses using Overpass API
- Returns the closest matching company with distance and reason
- If the company has a website, checks it and suggests the most related item/link to the request
- Generates a ready-to-send order/request message for the selected company

## Tech stack

- **Backend:** FastAPI (Python)
- **Frontend:** HTML/CSS/JS chat UI
- **Data source:** OpenStreetMap (Nominatim + Overpass)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open: <http://localhost:8000>

## OpenAI (optional)

To enable ChatGPT-enhanced replies, set your API key as an environment variable (never hardcode it in code or HTML):

```bash
export OPENAI_API_KEY="your_key_here"
```

The app will still work without this key and will fall back to the built-in response formatting.

## API

### `POST /api/chat`

Request body:

```json
{
  "message": "I need coffee near Austin"
}
```

Response body:

```json
{
  "reply": "Best option: Starbucks...",
  "intent": "coffee",
  "location": "Austin",
  "company": {
    "name": "Starbucks",
    "distance_km": 0.53,
    "address": "..."
  }
}
```
