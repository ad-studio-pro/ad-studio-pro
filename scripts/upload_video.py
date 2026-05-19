"""
Video uploader — uploads MP4 files to a public URL so BytePlus can fetch
them as `reference_video`.

Default backend: catbox.moe (free, no auth, anonymous, accepts MP4).
"""

import requests
from pathlib import Path


def upload_video_to_catbox(video_path: Path) -> str:
    """Upload an MP4 to catbox.moe. Returns the public URL."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    with open(video_path, "rb") as f:
        files = {"fileToUpload": (video_path.name, f, "video/mp4")}
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
        print(f"[OK] Video uploaded -> {url}")
        return url


def upload_video(video_path: Path) -> str:
    """Single entry point. Picks a backend."""
    return upload_video_to_catbox(video_path)
