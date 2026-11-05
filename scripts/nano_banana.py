"""
Nano Banana 2 wrapper — Google Gemini 2.5 Flash Image.

Use cases in the pipeline:
1. Generate scene reference images for Seedance (some formats need a hero
   product still that's bigger/different from what the user uploaded).
2. Generate character sheets if Stage 3 needs a consistent on-screen persona.

API: https://aistudio.google.com/apikey
"""

import os
import base64
import time
import requests
from pathlib import Path
from datetime import datetime
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

# Model discovery: Google renames image models often (2.5-flash-image-preview →
# 2.5-flash-image → 3.1-flash-image ...). We resolve at runtime via ListModels,
# with a preference-ordered fallback chain. Override with GEMINI_IMAGE_MODEL env.
_FALLBACK_IMAGE_MODELS = [
    "gemini-3.1-flash-image",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
    "gemini-2.5-flash-image-preview",
]
_MODEL_CACHE = {"resolved": None}


def _discover_image_model(key, log=print):
    """Pick the best available image-generation model for this API key."""
    if _MODEL_CACHE["resolved"]:
        return _MODEL_CACHE["resolved"]
    override = _get("GEMINI_IMAGE_MODEL", "")
    if override:
        _MODEL_CACHE["resolved"] = override
        return override
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={key}&pageSize=200",
            timeout=30,
        )
        if r.status_code < 400:
            names = []
            for m in r.json().get("models", []):
                short = m.get("name", "").split("/")[-1]
                methods = m.get("supportedGenerationMethods") or []
                if "image" in short.lower() and "generateContent" in methods:
                    names.append(short)
            for pref in _FALLBACK_IMAGE_MODELS:
                if pref in names:
                    _MODEL_CACHE["resolved"] = pref
                    log(f"  🎨 image model: {pref}")
                    return pref
            if names:
                names.sort(reverse=True)
                _MODEL_CACHE["resolved"] = names[0]
                log(f"  🎨 image model (auto): {names[0]}")
                return names[0]
    except Exception as e:
        log(f"  ⚠ ListModels failed: {e}")
    return _FALLBACK_IMAGE_MODELS[0]


GEMINI_IMAGE_MODEL = _FALLBACK_IMAGE_MODELS[0]  # backward-compat default


def generate_scene_image(
    prompt: str,
    reference_image_paths: list = None,
    output_path: Path = None,
    log=print,
) -> Path:
    """
    Generate a scene image from text prompt + optional reference image(s).

    Args:
        prompt: full text description of the scene to generate.
        reference_image_paths: optional list of input images (the product image,
            a character reference, etc.). Gemini uses them as visual anchors.
        output_path: where to save the resulting PNG. Defaults to outputs/scenes/.

    Returns:
        Path to the saved PNG.
    """
    # Google Gemini is OFF unless ALLOW_GEMINI=1 is set in Secrets.
    # All app image creation goes through Seedream 5.0 (BytePlus — already paid).
    if not gemini_allowed():
        return _generate_with_seedream(prompt, reference_image_paths, output_path, log=log)
    gemini_key = _get("GEMINI_API_KEY", "")
    if not gemini_key:
        raise RuntimeError(
            "GEMINI_API_KEY missing. Set it in .env locally OR in Streamlit Cloud "
            "Settings -> Secrets. Get one at https://aistudio.google.com/apikey"
        )

    # Build content parts: text + reference images
    parts = [{"text": prompt}]
    if reference_image_paths:
        for ref in reference_image_paths:
            ref_path = Path(ref)
            if not ref_path.exists():
                log(f"   ⚠ skipping missing ref image: {ref_path}")
                continue
            with open(ref_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ext = ref_path.suffix.lower()
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
            parts.append({"inline_data": {"mime_type": mime, "data": b64}})

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "temperature": 0.7,
        },
    }

    # Try the resolved model first, then walk the fallback chain on 404.
    primary = _discover_image_model(gemini_key, log=log)
    candidates = [primary] + [m for m in _FALLBACK_IMAGE_MODELS if m != primary]
    response = None
    last_err = ""
    for model_name in candidates:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={gemini_key}"
        )
        log(f"  🎨 Generating image via {model_name}...")
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 404:
            last_err = response.text[:200]
            log(f"  ⚠ {model_name} not found — trying next model")
            continue
        if response.status_code == 402 or "RESOURCE_EXHAUSTED" in response.text[:400]:
            raise RuntimeError(
                "The Google Gemini (Nano Banana) image credits ran out. This is an OPTIONAL helper "
                "(reference sheets / auto-split) — video generation on Seedance is not affected. "
                "To use it again, top up credits at https://aistudio.google.com/ (Billing), "
                "or skip this step and upload your images as they are."
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Nano Banana failed [{response.status_code}]: {response.text[:400]}"
            )
        _MODEL_CACHE["resolved"] = model_name  # remember the winner
        break
    else:
        raise RuntimeError(f"No available Gemini image model. Last error: {last_err}")

    data = response.json()

    # Find the inline image in the response
    image_b64 = None
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "inline_data" in part or "inlineData" in part:
                inline = part.get("inline_data") or part.get("inlineData")
                image_b64 = inline.get("data")
                break
        if image_b64:
            break

    if not image_b64:
        raise RuntimeError(f"No image in Gemini response: {str(data)[:400]}")

    # Save
    if output_path is None:
        output_dir = PROJECT_ROOT / "outputs" / "scenes"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"scene_{timestamp}.png"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_bytes(base64.b64decode(image_b64))
    size_kb = output_path.stat().st_size / 1024
    log(f"  ✓ saved {output_path.name} ({size_kb:.0f} KB)")
    return output_path


def gemini_allowed() -> bool:
    """Gemini (Google) is disabled by default — the owner doesn't want it used."""
    return _get("ALLOW_GEMINI", "").strip() == "1" and bool(_get("GEMINI_API_KEY"))


def is_available() -> bool:
    """Image creation available? (Seedream via the ARK key, or Gemini if allowed)."""
    return bool(_get("ARK_API_KEY") or _get("BYTEPLUS_API_KEY")) or gemini_allowed()


def _generate_with_seedream(prompt, reference_image_paths=None, output_path=None, log=print):
    """Same contract as generate_scene_image, but on Seedream 5.0 lite (BytePlus)."""
    from byteplus_client import seedream_from_images
    from upload_image import upload_image
    refs = []
    for ref in (reference_image_paths or []):
        if Path(ref).exists():
            refs.append(upload_image(Path(ref), log=log))   # normalized data: URL
    log(f"  🎨 Generating image via Seedream 5.0 lite ({len(refs)} reference image(s))...")
    url = seedream_from_images(prompt, refs)
    out = Path(output_path) if output_path else Path("outputs/scenes") / f"scene_{abs(hash(prompt)) % 10**8}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    out.write_bytes(r.content)
    log(f"  ✓ saved {out.name}")
    return out


if __name__ == "__main__":
    print(f"GEMINI_API_KEY: {'✓' if _get('GEMINI_API_KEY') else '✗ MISSING'}")
    print(f"Model: {GEMINI_IMAGE_MODEL}")
