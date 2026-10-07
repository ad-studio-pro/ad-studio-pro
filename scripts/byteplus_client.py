"""
BytePlus ModelArk client for Seedance 2.0
Async submit -> poll -> download workflow.
"""

import os
import time
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
    """Read config from env first, then Streamlit secrets, then default."""
    val = os.getenv(key)
    if val:
        return val
    return _SECRETS.get(key, default)


def _api_key():
    """Lazy lookup so import doesn't fail before Streamlit loads secrets."""
    k = _get("ARK_API_KEY")
    if not k:
        raise RuntimeError(
            "ARK_API_KEY missing. Set it in .env locally OR in Streamlit Cloud "
            "Settings -> Secrets."
        )
    return k


def _base_url():
    return _get("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3").rstrip("/")


def _model_id():
    return _get("SEEDANCE_MODEL_ID", "dreamina-seedance-2-0-260128")


def _model_id_25():
    """Seedance 2.5 — native 30s single take. Same ARK endpoint + key."""
    return _get("SEEDANCE_MODEL_ID_25", "dreamina-seedance-2-5-260628")


def model_for_engine(engine: str) -> str:
    """engine: "2.5" -> Seedance 2.5 model id, anything else -> 2.0."""
    return _model_id_25() if str(engine) == "2.5" else _model_id()


def max_single_duration(engine: str) -> int:
    """Longest clip one generation can produce: 2.5 = 30s, 2.0 = 15s."""
    return 30 if str(engine) == "2.5" else 15


def _headers():
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


# Backwards-compatible module attributes (deprecated, prefer the _get() helpers).
ARK_API_KEY = _get("ARK_API_KEY")
ARK_BASE_URL = _get("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3").rstrip("/")
SEEDANCE_MODEL_ID = _get("SEEDANCE_MODEL_ID", "dreamina-seedance-2-0-260128")


def submit_task(prompt, image_urls=None, video_urls=None, audio_urls=None,
                *, model=None, ratio="9:16", duration=15,
                generate_audio=True, watermark=False, extra_payload=None):
    """Submit a video generation task. Returns task_id."""
    content = [{"type": "text", "text": prompt}]

    for url in (image_urls or [])[:9]:
        content.append({"type": "image_url", "image_url": {"url": url}, "role": "reference_image"})
    for url in (video_urls or [])[:3]:
        content.append({"type": "video_url", "video_url": {"url": url}, "role": "reference_video"})
    for url in (audio_urls or [])[:3]:
        content.append({"type": "audio_url", "audio_url": {"url": url}, "role": "reference_audio"})

    payload = {
        "model": model or _model_id(),
        "content": content,
        "ratio": ratio,
        "duration": duration,
        "generate_audio": generate_audio,
        "watermark": watermark,
    }
    if extra_payload:
        payload.update(extra_payload)

    url = f"{_base_url()}/contents/generations/tasks"
    # 120s timeout — BytePlus needs to fetch + verify reference media before
    # returning a task_id; 30s wasn't enough for video references.
    response = requests.post(url, json=payload, headers=_headers(), timeout=120)

    # Inline (base64) images are the primary path. If ModelArk refuses them for
    # a format/parameter reason (NOT the face filter), re-host them on a public
    # URL and retry once.
    if response.status_code >= 400:
        _b = (response.text or "")
        _has_inline = any(
            c.get("type") == "image_url" and str(c["image_url"]["url"]).startswith("data:")
            for c in content)
        if (_has_inline and "image" in _b.lower() and "Sensitive" not in _b):
            try:
                import base64 as _b64
                from upload_image import host_image_bytes
                for c in content:
                    if c.get("type") == "image_url" and str(c["image_url"]["url"]).startswith("data:"):
                        raw = _b64.b64decode(c["image_url"]["url"].split(",", 1)[1])
                        c["image_url"]["url"] = host_image_bytes(raw, "ref.jpg")
                print("[..] inline images refused — retrying with hosted URLs")
                response = requests.post(url, json=payload, headers=_headers(), timeout=120)
            except Exception as _he:
                print(f"[!!] re-hosting images failed: {_he}")

    if response.status_code >= 400:
        body = response.text or ""
        # Friendly hint: real-person filter on reference IMAGE (check FIRST —
        # image errors also carry the generic "PrivacyInformation" code)
        if "InputImageSensitiveContentDetected" in body or "input image" in body.lower():
            raise RuntimeError(
                "❌ Seedance blocked one or more reference IMAGES — its classifier "
                "read them as photos of a real person.\n"
                "💡 If these are AI characters: use '🪄 Prepare AI characters' (or let "
                "the auto-retry run) — it re-renders the SAME character slightly "
                "stylized so it clearly reads as a digital character.\n"
                "Also make sure the same face image isn't uploaded twice (e.g. both as "
                "a product image and as an AI character).\n\n"
                f"Source: {body[:400]}"
            )
        # Friendly hint: real-person filter on reference video
        if "InputVideoSensitiveContentDetected" in body or "PrivacyInformation" in body:
            raise RuntimeError(
                "❌ Seedance blocked the reference video because it detected a real person's face "
                "(ByteDance's anti-deepfake mechanism — cannot be bypassed).\n\n"
                "💡 Solutions:\n"
                "  1. Use a reference video without realistic faces (product only / animation / abstract).\n"
                "     Note: AI-generated characters usually pass, but VERY photorealistic AI faces can\n"
                "     still trigger the filter — regenerate the character slightly stylized if needed\n"
                "  2. Remove the reference video entirely — Seedance will generate from the prompt+image\n"
                "  3. Blur/crop faces out of the video in CapCut/Premiere before uploading\n\n"
                f"Source: {body[:400]}"
            )
        # Friendly hint: real-person filter on reference IMAGE
        # Friendly hint: resolution not supported by the chosen model
        _low = body.lower()
        if ("resolution" in _low and ("invalidparameter" in _low or "not support" in _low
                                       or "unsupported" in _low)):
            _res = str((extra_payload or {}).get("resolution", "?"))
            raise RuntimeError(
                f"❌ Seedance rejected the resolution '{_res}' for this model.\n"
                "💡 Step down one level (1080p → 720p → 480p) in the 'Video quality' box, "
                "or switch engine — resolution support differs between Seedance 2.0 and 2.5 "
                "and changes as ByteDance rolls out updates.\n\n"
                f"Source: {body[:300]}"
            )
        if ("ModelNotFound" in body or "model not found" in body.lower()
                or ("InvalidParameter" in body and "model" in body.lower() and "seedance-2-5" in str(payload.get("model", "")))):
            raise RuntimeError(
                "❌ Seedance 2.5 is not enabled on your ModelArk account yet "
                "(the API opens gradually after the Jul 31 launch).\n"
                "💡 Switch the engine back to Seedance 2.0 and try again, or check "
                "the BytePlus console → ModelArk → Model list for 2.5 availability.\n\n"
                f"Source: {body[:300]}"
            )
        if "UnsupportedImageFormat" in body:
            raise RuntimeError(
                "❌ Seedance couldn't read one of the reference images as an image.\n"
                "💡 Re-save the image as a regular JPG/PNG (e.g. screenshot it) and upload again.\n\n"
                f"Source: {body[:300]}"
            )
        raise RuntimeError(f"BytePlus submit failed [{response.status_code}]: {body}")

    data = response.json()
    task_id = (data.get("id") or data.get("task_id") or data.get("request_id")
               or data.get("data", {}).get("id"))
    if not task_id:
        raise RuntimeError(f"No task_id in response: {data}")

    print(f"[OK] Task submitted: {task_id}")
    return task_id


def poll_task(task_id, interval=15, max_wait=900, log=print):
    """Poll task until succeeded/failed. Returns the full task object.

    Args:
        log: callback for progress messages. Default = print to stdout.
             Pass a Streamlit status.write or any other callable.
    """
    url = f"{_base_url()}/contents/generations/tasks/{task_id}"
    elapsed = 0
    log(f"   ⏳ Waiting... typical: 60-180 seconds, updates every {interval}s")

    while elapsed < max_wait:
        response = requests.get(url, headers=_headers(), timeout=30)
        if response.status_code >= 400:
            raise RuntimeError(f"BytePlus poll failed [{response.status_code}]: {response.text}")
        data = response.json()

        status = (data.get("status") or "").lower()

        # Friendly status display
        emoji = {"running": "⚙️", "queued": "📋", "pending": "📋",
                 "succeeded": "✅", "completed": "✅", "success": "✅",
                 "failed": "❌", "error": "❌"}.get(status, "•")
        log(f"   {emoji} status={status}  ({elapsed}s elapsed)")

        if status in ("succeeded", "completed", "success"):
            return data
        if status in ("failed", "error", "cancelled", "canceled"):
            err = data.get("error", data)
            err_str = str(err)
            # Friendly hint for the audio safety filter
            if "OutputAudioSensitive" in err_str:
                raise RuntimeError(
                    "Task failed: Seedance's audio safety filter blocked this output.\n"
                    "💡 Fix: in Express, uncheck '🔊 Generate audio' and try again.\n"
                    f"Source: {err_str}"
                )
            raise RuntimeError(f"Task failed: {err}")

        time.sleep(interval)
        elapsed += interval

    raise TimeoutError(f"Task {task_id} did not complete within {max_wait}s")


def download_video(video_url, output_path):
    """Download video from temporary URL (24h expiry!) to local file."""
    output_path = Path(output_path)
    print(f"[..] Downloading -> {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(video_url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 14):
                if chunk:
                    f.write(chunk)

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"[OK] Saved {output_path.name}  ({size_mb:.1f} MB)")
    return output_path


def extract_video_url(task_result):
    """Try multiple shapes BytePlus might use for the video URL."""
    candidates = [
        task_result.get("content", {}).get("video_url"),
        task_result.get("output", {}).get("video_url"),
        task_result.get("output", {}).get("media_url"),
        task_result.get("video_url"),
        task_result.get("result", {}).get("video_url"),
        task_result.get("data", {}).get("video_url"),
    ]
    for u in candidates:
        if u and isinstance(u, str):
            return u
    raise RuntimeError(
        f"No video URL in result. Top-level keys: {list(task_result.keys())}\n"
        f"Result snippet: {json.dumps(task_result, ensure_ascii=False)[:600]}"
    )


def test_connection():
    """Submit a tiny no-reference task to verify auth + endpoint + model name."""
    key = _get("ARK_API_KEY")
    masked = key[:8] + "..." + key[-4:] if key else "(missing)"
    print(f"Base URL : {_base_url()}")
    print(f"Model    : {_model_id()}")
    print(f"API Key  : {masked}")
    print()

    try:
        task_id = submit_task(
            prompt="A single red apple sits on a clean white table. Soft natural daylight from one side. Static camera. 5 seconds.",
            duration=5,
            ratio="1:1",
        )
        print(f"[OK] Connection works. Test task_id: {task_id}")
        print("     (Task left running in BytePlus — safe to ignore.)")
        return task_id
    except Exception as exc:
        print(f"[FAIL] {exc}")
        raise


if __name__ == "__main__":
    test_connection()


# ─────────────────────────────────────────────────────────────────────────────
# Trusted inputs (official ByteDance face support)
#   • Seedream 5.0 lite text-to-image outputs and Seedance video outputs created
#     on THIS ModelArk account are trusted as face-containing inputs for 30 days
#     — but only as the ORIGINAL file (pass the returned URL untouched; never
#     download+re-upload/compress, which voids the trust).
#   • Private asset library items are referenced as asset://<asset ID>.
# ─────────────────────────────────────────────────────────────────────────────

def _seedream_model_id():
    return _get("SEEDREAM_MODEL_ID", "seedream-5-0-260128")


def seedream_generate(prompt, size="2K", model=None, timeout=180):
    """Text-to-image with Seedream 5.0 lite on ModelArk. Returns the ORIGINAL
    image URL (≈24h valid) — use it as-is as a trusted Seedance reference."""
    payload = {
        "model": model or _seedream_model_id(),
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "watermark": False,
    }
    r = requests.post(f"{_base_url()}/images/generations", json=payload,
                      headers=_headers(), timeout=timeout)
    if r.status_code >= 400:
        body = r.text or ""
        if "ModelNotOpen" in body or "not activated" in body.lower() or "NotFound" in body:
            raise RuntimeError(
                "❌ Seedream 5.0 lite isn't activated on this ModelArk account.\n"
                "💡 BytePlus console → ModelArk → Model activation → enable Seedream 5.0 lite.\n\n"
                f"Source: {body[:300]}")
        raise RuntimeError(f"Seedream failed [{r.status_code}]: {body[:400]}")
    data = r.json()
    items = data.get("data") or []
    url = items[0].get("url") if items else None
    if not url:
        raise RuntimeError(f"No image URL in Seedream response: {str(data)[:300]}")
    return url


def normalize_asset_ref(text):
    """'asset-2026…' / 'asset://asset-2026…' → 'asset://asset-2026…' (else None)."""
    t = (text or "").strip()
    if not t:
        return None
    if t.startswith("asset://"):
        return t
    if t.startswith("asset-"):
        return "asset://" + t
    return None
