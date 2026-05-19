"""
Stage 1 — Trend Research & Product Auto-Detect

Inputs:  product image + optional URL
Outputs: detected category, niche, audience defaults, viral content brief

Pipeline:
  1. Gemini Vision: auto-detect category, SKUs, packaging, region cues from product image
  2. Tavily web search: pull live trend data for the detected niche
  3. Compose the "Viral Content Brief" using Claude.ai (via CDP) with skill rules

Module API:
  detect_product(image_path) -> dict            (Gemini Vision)
  research_trends(niche) -> dict                (Tavily web search)
  compose_brief(product, trends, ...) -> str    (Claude.ai via CDP)
"""

import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Streamlit Cloud fallback.
try:
    import streamlit as st
    _SECRETS = dict(st.secrets) if hasattr(st, "secrets") else {}
except Exception:
    _SECRETS = {}


def _get(key, default=""):
    val = os.getenv(key)
    if val:
        return val
    return _SECRETS.get(key, default)


GEMINI_API_KEY = _get("GEMINI_API_KEY", "")
TAVILY_API_KEY = _get("TAVILY_API_KEY", "")


# ─── Gemini Vision: product detection ──────────────────────────────────────

GEMINI_VISION_PROMPT = """You are a product analyst. Examine this image and return ONLY a JSON object describing the product. No commentary, no markdown fences — just the JSON.

Fields (all required):
{
  "category": "one of: jewelry, beverage, skincare, haircare, makeup, apparel, footwear, eyewear, food, electronics, appliance, home, supplements, pet, software_app, service",
  "subtype": "more specific (e.g., 'silicone wedding ring', 'cold-pressed juice', 'vitamin C serum')",
  "skus_visible": ["array of SKU / variant descriptions visible — flavors, colors, sizes, scents"],
  "brand_name_visible": "exact brand text if visible on packaging, else empty string",
  "packaging_colors": ["array of dominant brand colors as common color names"],
  "packaging_style": "premium / Gen-Z playful / wellness / luxury / functional / handmade / clinical",
  "region_cue": "global / IL / MENA / CIS / CN / SEA / LatAm — inferred from any text on packaging",
  "niche_keyword": "short English phrase (e.g., 'silicone wedding ring', 'matcha latte powder', 'vitamin C serum')",
  "audience_default": "American / Israeli / Pan-Arab / Slavic / East-Asian / Latin-American / Mixed international"
}

Return ONLY the JSON. No backticks, no explanation."""


def detect_product(image_path: Path) -> dict:
    """Use Gemini 2.5 Flash to auto-detect product details from image."""
    gemini_key = _get("GEMINI_API_KEY", "")
    if not gemini_key:
        raise RuntimeError(
            "GEMINI_API_KEY missing. Set it in .env locally OR in Streamlit Cloud "
            "Settings -> Secrets. Get one at https://aistudio.google.com/apikey"
        )

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    # Encode image as base64
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    # Detect mime type
    ext = image_path.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={gemini_key}"
    )

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": GEMINI_VISION_PROMPT},
                {"inline_data": {"mime_type": mime, "data": image_b64}},
            ],
        }],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }

    response = requests.post(url, json=payload, timeout=60)
    if response.status_code >= 400:
        raise RuntimeError(f"Gemini Vision failed [{response.status_code}]: {response.text[:400]}")

    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]

    # Parse the JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Strip any markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())


# ─── Tavily: live trend research ───────────────────────────────────────────

TREND_QUERIES = [
    "{niche} TikTok trending videos this week {month} {year}",
    "viral {niche} content Instagram Reels {month} {year}",
    "{niche} YouTube Shorts trending {month} {year}",
    "{niche} brand content going viral {month} {year}",
    "top {niche} ads performing {month} {year}",
    "{niche} UGC content trend {month} {year}",
    "{niche} hooks that stop the scroll {month} {year}",
    "{niche} competitor brands social media strategy {month} {year}",
]


def research_trends(niche: str, max_results_per_query: int = 3, log=print) -> dict:
    """Run all 8 trend queries via Tavily, return aggregated findings."""
    tavily_key = _get("TAVILY_API_KEY", "")
    if not tavily_key:
        raise RuntimeError(
            "TAVILY_API_KEY missing. Set it in .env locally OR in Streamlit Cloud "
            "Settings -> Secrets. Get one at https://tavily.com/"
        )

    from datetime import datetime
    now = datetime.now()
    month = now.strftime("%B")
    year = now.strftime("%Y")

    all_results = []
    for q_template in TREND_QUERIES:
        query = q_template.format(niche=niche, month=month, year=year)
        log(f"  🔎 {query[:80]}...")
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "max_results": max_results_per_query,
                    "search_depth": "basic",
                    "include_answer": True,
                },
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                all_results.append({
                    "query": query,
                    "answer": data.get("answer", ""),
                    "results": [
                        {"title": r.get("title"), "url": r.get("url"),
                         "snippet": r.get("content", "")[:300]}
                        for r in data.get("results", [])
                    ],
                })
            else:
                log(f"     ⚠ {response.status_code}: {response.text[:100]}")
        except Exception as e:
            log(f"     ⚠ error: {e}")

    return {"month": month, "year": year, "queries": all_results}


# ─── Quick smoke test ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"GEMINI_API_KEY: {'✓' if _get('GEMINI_API_KEY') else '✗ MISSING'}")
    print(f"TAVILY_API_KEY: {'✓' if _get('TAVILY_API_KEY') else '✗ MISSING'}")
