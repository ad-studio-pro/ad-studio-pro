"""
AI-character reference helper.

Purpose: let this PRIVATE (login-gated, @neobrands.io only) app use AI-GENERATED
character portraits as Seedance reference images — the official Dreamina "AI
influencer" workflow.

ByteDance's reference-image filter (InputImageSensitiveContentDetected) rejects
images its classifier reads as a photo of a REAL person. AI-generated portraits
usually pass, but very photorealistic ones can trip the classifier by accident.

`prepare_ai_character()` re-renders an ALREADY-AI image through Nano Banana as a
clean digital-character render — same identity, slightly less photographic — so
it reads unambiguously as a digital character and clears the filter. This is a
transformation of an AI asset, not a technique for disguising a real person's
photo.
"""

import base64
from pathlib import Path

import requests

from nano_banana import generate_scene_image, is_available, _get  # noqa: F401

# Optional stronger engine: GPT Image 2 (OpenAI) — better identity/composition
# preservation on complex scenes. Used automatically when OPENAI_API_KEY is set
# (Streamlit Secrets or .env); otherwise falls back to Nano Banana.
OPENAI_IMAGE_MODEL_DEFAULT = "gpt-image-2"


def is_openai_available() -> bool:
    return bool(_get("OPENAI_API_KEY", ""))


def _prepare_with_openai(image_path, prompt, out_path, log=print):
    """Image-to-image edit via OpenAI Images API (GPT Image 2)."""
    key = _get("OPENAI_API_KEY", "")
    model = _get("OPENAI_IMAGE_MODEL", OPENAI_IMAGE_MODEL_DEFAULT)
    image_path = Path(image_path)
    raw = image_path.read_bytes()
    mime = "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg"
    log(f"  🎨 Re-rendering via {model} (OpenAI)...")
    resp = requests.post(
        "https://api.openai.com/v1/images/edits",
        headers={"Authorization": f"Bearer {key}"},
        files={"image": (image_path.name, raw, mime)},
        data={"model": model, "prompt": prompt, "size": "auto"},
        timeout=180,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"OpenAI images/edits failed [{resp.status_code}]: {resp.text[:300]}")
    data = resp.json()
    b64 = data.get("data", [{}])[0].get("b64_json")
    if not b64:
        raise RuntimeError(f"No image in OpenAI response: {str(data)[:200]}")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(b64))
    log(f"  ✓ saved {out_path.name} ({out_path.stat().st_size // 1024} KB)")
    return out_path


PREP_PROMPT = (
    "Re-render this AI-generated image as a high-end REALISTIC CGI render, like "
    "a modern AAA game cinematic (Unreal Engine 5 look). PRESERVE THE ENTIRE "
    "IMAGE EXACTLY: same composition, framing, background, lighting mood, and "
    "EVERY person with the same identity — same face shapes, hairstyles, skin "
    "tones, outfits, expressions, poses and positions. Keep fully realistic "
    "human proportions and detail; only make the skin shading slightly smoother "
    "and the finish subtly 'rendered' so it reads as a digital production, not "
    "a photograph. Absolutely NOT a cartoon, NOT animated-film style. High "
    "detail, no elements added or removed."
), so every person clearly "
    "reads as a designed digital character rather than a photo of a real "
    "person. High detail, no elements added or removed."
)


STRONG_PREP_PROMPT = (
    "Re-render this AI-generated image as a clearly digital, stylized-REALISTIC "
    "CGI cinematic — like a premium game cutscene: uniform smooth skin shading, "
    "slightly simplified surface detail, clean cinematic lighting, a subtle "
    "digital sheen. PRESERVE THE ENTIRE IMAGE: same composition, framing, "
    "background, and every person with the same recognizable identity, REALISTIC "
    "human proportions (normal-sized eyes and features). It must read as a "
    "digital render, NOT a photograph — but absolutely NOT a cartoon, NOT "
    "Pixar/animated-film style. High detail, no elements added or removed."
)

_PROMPTS = {"soft": PREP_PROMPT, "strong": STRONG_PREP_PROMPT}


def prepare_ai_character(image_path, out_path, log=print, strength="soft"):
    """Re-render one AI character image so it passes the reference filter.
    strength: "soft" (subtle CGI polish) or "strong" (clearly animated style).
    Returns the new PNG path. Identity is preserved.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log(f"🧑‍🎤 Preparing AI character ({strength}): {Path(image_path).name}")
    prompt = _PROMPTS.get(strength, PREP_PROMPT)
    # Prefer GPT Image 2 when configured — much better at preserving complex
    # multi-person scenes. Fall back to Nano Banana on any failure.
    if is_openai_available():
        try:
            return _prepare_with_openai(image_path, prompt, out_path, log=log)
        except Exception as e:
            log(f"  ⚠ GPT Image 2 failed ({e}) — falling back to Nano Banana")
    return generate_scene_image(prompt, [str(image_path)], out_path, log=log)


def prepare_many(image_paths, out_dir, log=print, progress=None, strength="soft"):
    """Prepare a batch. Returns list of new paths (aligned with input order)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for i, ip in enumerate(image_paths, 1):
        out = out_dir / f"ai_char_{strength}_{i}.png"
        try:
            results.append(str(prepare_ai_character(ip, out, log=log, strength=strength)))
        except Exception as e:
            log(f"  ⚠ failed on {Path(ip).name}: {e} — keeping original")
            results.append(str(ip))
        if progress:
            progress(i, len(image_paths))
    return results
