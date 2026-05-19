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

# Streamlit Cloud fallback: secrets are in st.secrets, not os.environ.
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


def _api_key():
    return _get("ANTHROPIC_API_KEY", "")


def _model():
    return _get("ANTHROPIC_MODEL", "claude-opus-4-6")


# Backwards-compatible module attributes.
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = _get("ANTHROPIC_MODEL", "claude-opus-4-6")


def is_available() -> bool:
    return bool(_api_key())


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
    api_key = _api_key()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY missing. Set it in .env locally OR in "
            "Streamlit Cloud Settings -> Secrets. "
            "Get a key at https://console.anthropic.com/"
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

    model = _model()
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        payload["system"] = system

    log(f"  [anthropic] {model} — {len(content)} content blocks, {len(user_message)} chars")
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
    print(f"ANTHROPIC_API_KEY: {'✓' if _api_key() else '✗ MISSING'}")
    print(f"Model: {_model()}")
