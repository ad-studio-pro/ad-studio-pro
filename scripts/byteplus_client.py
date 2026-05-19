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

ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3").rstrip("/")
SEEDANCE_MODEL_ID = os.getenv("SEEDANCE_MODEL_ID", "dreamina-seedance-2-0-260128")

if not ARK_API_KEY:
    raise RuntimeError("ARK_API_KEY missing in .env")

HEADERS = {
    "Authorization": f"Bearer {ARK_API_KEY}",
    "Content-Type": "application/json",
}


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
        "model": model or SEEDANCE_MODEL_ID,
        "content": content,
        "ratio": ratio,
        "duration": duration,
        "generate_audio": generate_audio,
        "watermark": watermark,
    }
    if extra_payload:
        payload.update(extra_payload)

    url = f"{ARK_BASE_URL}/contents/generations/tasks"
    response = requests.post(url, json=payload, headers=HEADERS, timeout=30)

    if response.status_code >= 400:
        raise RuntimeError(f"BytePlus submit failed [{response.status_code}]: {response.text}")

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
    url = f"{ARK_BASE_URL}/contents/generations/tasks/{task_id}"
    elapsed = 0
    log(f"   ⏳ ממתין... typical: 60-180 שניות, מתעדכן כל {interval}s")

    while elapsed < max_wait:
        response = requests.get(url, headers=HEADERS, timeout=30)
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
            raise RuntimeError(f"Task failed: {data.get('error', data)}")

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
    masked = ARK_API_KEY[:8] + "..." + ARK_API_KEY[-4:] if ARK_API_KEY else "(missing)"
    print(f"Base URL : {ARK_BASE_URL}")
    print(f"Model    : {SEEDANCE_MODEL_ID}")
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
