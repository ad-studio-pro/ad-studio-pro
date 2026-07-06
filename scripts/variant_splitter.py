"""
Variant splitter — turns ONE group photo (e.g. a stack of 7 ring colors)
into separate per-variant product images with auto-detected names.

Pipeline:
  1. detect_variants()  — Gemini 2.5 Flash vision: lists each distinct variant.
  2. extract_variants() — Nano Banana (Gemini image gen) renders each variant
     as a clean standalone product photo on a white studio background,
     anchored to the original photo so colors/materials match exactly.

Used by Express mode when the user uploads a single multi-variant photo.
"""

import base64
import json
import re
from pathlib import Path

import requests

from nano_banana import _get, generate_scene_image

DETECT_MODEL = "gemini-2.5-flash"

_MIMES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
          ".png": "image/png", ".webp": "image/webp"}


def detect_variants(image_path, log=print) -> list:
    """Ask Gemini vision to list the distinct product variants in the photo.
    Returns a list of short English names (max 9)."""
    key = _get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")

    image_path = Path(image_path)
    b64 = base64.b64encode(image_path.read_bytes()).decode()
    mime = _MIMES.get(image_path.suffix.lower(), "image/jpeg")

    prompt = (
        "This is a product photo that may show SEVERAL variants of the same "
        "product (different colors / patterns / models). List each DISTINCT "
        "variant you can actually see. Return ONLY a JSON array of short "
        "English names that mention the color/pattern and product type, e.g. "
        '["black silicone ring", "white marble silicone ring"]. '
        "If there is only one variant, return an array with one item. "
        "No commentary, JSON only."
    )
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{DETECT_MODEL}:generateContent?key={key}")
    payload = {"contents": [{"role": "user", "parts": [
        {"text": prompt},
        {"inline_data": {"mime_type": mime, "data": b64}},
    ]}]}
    log("🔍 Gemini מזהה את הווריאציות בתמונה...")
    r = requests.post(url, json=payload, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Gemini detect failed [{r.status_code}]: {r.text[:300]}")
    data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        raise RuntimeError(f"No JSON array in Gemini reply: {text[:200]}")
    names = [str(n).strip() for n in json.loads(m.group(0)) if str(n).strip()]
    return names[:9]


def extraction_prompt(name: str) -> str:
    return (
        f"From the attached photo, extract ONLY the {name} as a standalone "
        "product photo: the single item centered on a seamless white studio "
        "background, three-quarter angle facing the camera, soft even studio "
        "lighting, subtle contact shadow, photorealistic commercial product "
        "photography, high detail.\n"
        "CRITICAL — CATALOG CONSISTENCY: all the variants in this set are the "
        "SAME product model in different colors. Render this one with IDENTICAL "
        "geometry to how it appears in the attached photo — identical band "
        "width, identical thickness, identical diameter and proportions — shot "
        "from the SAME camera distance and SAME angle as a standard catalog "
        "set, the item filling about 60% of the frame width. ONLY the "
        "color/pattern differs between variants.\n"
        "It must match its appearance in the attached photo EXACTLY — same "
        "color, same pattern, same material. No other items in the frame, "
        "no props, no text, no size variation."
    )


def extract_variants(image_path, names, out_dir, log=print, progress=None) -> list:
    """Generate one clean product image per variant. Returns [(path, name)]."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for i, name in enumerate(names, 1):
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or f"v{i}"
        out = out_dir / f"variant_{i}_{slug}.png"
        log(f"✂️ {i}/{len(names)} — {name}")
        generate_scene_image(extraction_prompt(name), [str(image_path)], out, log=log)
        results.append((str(out), name))
        if progress:
            progress(i, len(names))
    return results


def name_images(image_paths, log=print) -> list:
    """One Gemini vision call: short English name per attached image, in order."""
    key = _get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")
    paths = [Path(p) for p in image_paths][:9]
    parts = [{"text": (
        f"Attached are {len(paths)} product photos, ONE variant per photo, in order. "
        "Return ONLY a JSON array of exactly that many short English names, one per "
        "photo IN THE SAME ORDER, each naming the color/pattern + product type, e.g. "
        '["black silicone ring", "leopard print silicone ring"]. JSON only.'
    )}]
    for ip in paths:
        b64 = base64.b64encode(ip.read_bytes()).decode()
        mime = _MIMES.get(ip.suffix.lower(), "image/jpeg")
        parts.append({"inline_data": {"mime_type": mime, "data": b64}})
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{DETECT_MODEL}:generateContent?key={key}")
    r = requests.post(url, json={"contents": [{"role": "user", "parts": parts}]}, timeout=90)
    if r.status_code >= 400:
        raise RuntimeError(f"Gemini naming failed [{r.status_code}]: {r.text[:300]}")
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        raise RuntimeError(f"No JSON array in reply: {text[:200]}")
    names = [str(n).strip() for n in json.loads(m.group(0))]
    names = (names + [""] * len(paths))[:len(paths)]
    return names
