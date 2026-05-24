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

    if response.status_code >= 400:
        body = response.text or ""
        # Friendly hint: real-person filter on reference video
        if "InputVideoSensitiveContentDetected" in body or "PrivacyInformation" in body:
            raise RuntimeError(
                "❌ Seedance חסם את הוידאו רפרנס כי הוא מזהה בו פנים של אדם אמיתי "
                "(מנגנון anti-deepfake של ByteDance, אי אפשר לעקוף).\n\n"
                "💡 פתרונות:\n"
                "  1. השתמש בוידאו רפרנס בלי פנים אמיתיים (מוצר בלבד / אנימציה / מופשט)\n"
                "  2. הסר את הוידאו רפרנס לגמרי — Seedance תיצור מהפרומט+תמונה\n"
                "  3. טשטש/חתוך פנים מהוידאו ב-CapCut/Premiere לפני העלאה\n\n"
                f"מקור: {body[:400]}"
            )
        # Friendly hint: real-person filter on reference IMAGE
        if "InputImageSensitiveContentDetected" in body:
            raise RuntimeError(
                "❌ Seedance חסם תמונת רפרנס כי היא מזהה פנים של אדם אמיתי.\n\n"
                "💡 השתמש בתמונה בלי פנים זיהויות, או טשטש את הפנים לפני העלאה.\n\n"
                f"מקור: {body[:400]}"
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
    log(f"   ⏳ ממתין... typical: 60-180 שניות, מתעדכן כל {interval}s")

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
                    "💡 פתרון: ב-Express הסר את הסימון של '🔊 ייצור אודיו' ונסה שוב.\n"
                    f"מקור: {err_str}"
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
