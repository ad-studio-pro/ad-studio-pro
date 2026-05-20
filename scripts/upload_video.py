"""
Video uploader — uploads MP4 files to a public URL so BytePlus can fetch
them as `reference_video`.

Default backend: catbox.moe (free, no auth, anonymous, accepts MP4).
Fallback: tmpfiles.org if catbox rejects.
"""

import re
import time
import requests
from pathlib import Path


def _safe_filename(name: str) -> str:
    """Strip spaces, parens, and other characters catbox sometimes rejects."""
    # Keep only [a-zA-Z0-9._-]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    base = re.sub(r"_+", "_", base).strip("_")
    if not base or "." not in base:
        base = f"video_{int(time.time())}.mp4"
    return base


def upload_video_to_catbox(video_path: Path) -> str:
    """Upload an MP4 to catbox.moe. Returns the public URL."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    safe_name = _safe_filename(video_path.name)

    last_error = None
    for attempt in range(2):
        try:
            with open(video_path, "rb") as f:
                files = {"fileToUpload": (safe_name, f, "video/mp4")}
                data = {"reqtype": "fileupload"}
                response = requests.post(
                    "https://catbox.moe/user/api.php",
                    data=data,
                    files=files,
                    timeout=300,
                )
                response.raise_for_status()
                url = response.text.strip()
                if not url.startswith("http"):
                    raise RuntimeError(f"Catbox response unexpected: {url}")
                print(f"[OK] Video uploaded to catbox -> {url}")
                return url
        except Exception as e:
            last_error = e
            print(f"[catbox attempt {attempt+1}] failed: {e}")
            time.sleep(1)

    raise RuntimeError(f"catbox upload failed after retries: {last_error}")


def upload_video_to_tmpfiles(video_path: Path) -> str:
    """Fallback host — tmpfiles.org (free, anonymous, 60 min retention)."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    safe_name = _safe_filename(video_path.name)
    with open(video_path, "rb") as f:
        files = {"file": (safe_name, f, "video/mp4")}
        response = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files=files,
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        # tmpfiles returns: { "status": "success", "data": { "url": "https://tmpfiles.org/abc123/file.mp4" } }
        raw_url = data.get("data", {}).get("url", "")
        if not raw_url:
            raise RuntimeError(f"tmpfiles response unexpected: {data}")
        # Convert from preview URL to direct download URL
        direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        print(f"[OK] Video uploaded to tmpfiles -> {direct_url}")
        return direct_url


def upload_video(video_path: Path) -> str:
    """Upload with catbox; fall back to tmpfiles if catbox fails."""
    try:
        return upload_video_to_catbox(video_path)
    except Exception as catbox_err:
        print(f"[upload_video] catbox failed → trying tmpfiles fallback. ({catbox_err})")
        try:
            return upload_video_to_tmpfiles(video_path)
        except Exception as tmp_err:
            raise RuntimeError(
                f"Both video hosts failed. catbox: {catbox_err}. tmpfiles: {tmp_err}"
            )
