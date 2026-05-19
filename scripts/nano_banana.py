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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image-preview"


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
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY missing in .env. Get one at https://aistudio.google.com/apikey"
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

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_IMAGE_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "temperature": 0.7,
        },
    }

    log(f"  🎨 Generating scene image via Nano Banana 2...")
    response = requests.post(url, json=payload, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Nano Banana failed [{response.status_code}]: {response.text[:400]}"
        )

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


def is_available() -> bool:
    return bool(GEMINI_API_KEY)


if __name__ == "__main__":
    print(f"GEMINI_API_KEY: {'✓' if GEMINI_API_KEY else '✗ MISSING'}")
    print(f"Model: {GEMINI_IMAGE_MODEL}")
