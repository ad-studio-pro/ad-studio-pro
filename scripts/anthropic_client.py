"""
Anthropic Claude API client — direct API calls (no Chrome needed).
Used in cloud deployments where Chrome CDP isn't available.

Get an API key at https://console.anthropic.com/
"""

import os
import base64
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")


def is_available() -> bool:
    return bool(ANTHROPIC_API_KEY)


def call_claude_api(user_message: str,
                     attachments: list = None,
                     system: str = None,
                     max_tokens: int = 8000,
                     log=print) -> str:
    """
    Single-turn call to Anthropic Messages API.
    Returns Claude's response text.

    Args:
        user_message: the prompt text
        attachments: list of image paths (.jpg/.png/.webp). Up to 20.
        system: optional system prompt
        max_tokens: response length cap
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY missing in .env. "
            "Get one at https://console.anthropic.com/"
        )

    # Build content blocks (images first, then text — Anthropic recommends this)
    content = []
    if attachments:
        for path in attachments[:20]:
            p = Path(path)
            if not p.exists():
                log(f"  (skipping missing attachment: {p})")
                continue
            ext = p.suffix.lower()
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".webp": "image/webp",
                    ".gif": "image/gif"}.get(ext)
            if not mime:
                log(f"  (skipping non-image attachment: {p})")
                continue
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": b64,
                },
            })

    content.append({"type": "text", "text": user_message})

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        payload["system"] = system

    log(f"  [anthropic] {ANTHROPIC_MODEL} — {len(content)} content blocks, {len(user_message)} chars")
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=300,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Anthropic API failed [{response.status_code}]: {response.text[:500]}")

    data = response.json()
    text = "".join(
        block.get("text", "")
        for block in data.get("content", [])
        if block.get("type") == "text"
    )
    log(f"  [anthropic] got response ({len(text)} chars)")
    return text


if __name__ == "__main__":
    print(f"ANTHROPIC_API_KEY: {'✓' if ANTHROPIC_API_KEY else '✗ MISSING'}")
    print(f"Model: {ANTHROPIC_MODEL}")
