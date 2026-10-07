"""
Trusted references — bookkeeping for ORIGINAL ModelArk output URLs.

ByteDance's official face support (Seedance 2.0 / 2.5):
  • Seedance videos (and their last frames) and Seedream 5.0 lite text-to-image
    images generated on the SAME ModelArk account are trusted as face-containing
    inputs for 30 days — only as the original file.
  • The original URLs themselves expire after ~24h, so we track creation time
    and only offer URLs that are still fresh.

Everything lives in st.session_state (per browser session).
"""

import time

import streamlit as st

URL_TTL_SECONDS = 23 * 3600  # stay safely inside the ~24h URL validity


def _store():
    return st.session_state.setdefault("_trusted_outputs", [])


def record(kind, url, label=""):
    """Remember an original ModelArk output. kind: 'video' | 'image'."""
    if not url or not str(url).startswith("http"):
        return
    items = _store()
    if any(i["url"] == url for i in items):
        return
    items.append({"kind": kind, "url": url, "label": label or kind, "ts": time.time()})


def active(kind=None):
    """Fresh (not yet expired) trusted outputs, newest first."""
    now = time.time()
    items = [i for i in _store()
             if now - i["ts"] < URL_TTL_SECONDS and (kind is None or i["kind"] == kind)]
    return sorted(items, key=lambda i: -i["ts"])


def age_label(item):
    mins = int((time.time() - item["ts"]) / 60)
    return f"{mins} min ago" if mins < 90 else f"{mins // 60} h ago"
