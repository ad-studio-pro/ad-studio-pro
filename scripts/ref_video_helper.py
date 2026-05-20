"""
Reference video helper — uploads user-uploaded reference videos to catbox
and caches the URLs. Stage 4 uses these as `video_urls` in submit_task.

Also handles auto-downscaling — BytePlus Seedance 2.0 rejects reference
videos whose pixel count exceeds ~2.08M (roughly 1080p). We auto-scale
larger videos down to fit before uploading.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import streamlit as st

try:
    from upload_video import upload_video as _upload_video
except Exception:
    _upload_video = None

# BytePlus Seedance 2.0 reference-video pixel cap
MAX_PIXELS = 2_086_876


def _ffmpeg_bin():
    """Return path to ffmpeg binary (via imageio-ffmpeg)."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _ffprobe_size(video_path: Path):
    """Return (width, height) of the video, or (None, None) on failure."""
    ffmpeg = _ffmpeg_bin()
    if not ffmpeg:
        return None, None
    try:
        # Use ffmpeg to dump info — parse stderr for "Stream ... Video: ... 1920x1080"
        result = subprocess.run(
            [ffmpeg, "-i", str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
        stderr = result.stderr
        # Look for "1920x1080" pattern in stream info
        import re
        m = re.search(r"\s(\d{3,5})x(\d{3,5})[,\s]", stderr)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return None, None


def _downscale_if_needed(video_path: Path, log=print) -> Path:
    """If the video exceeds MAX_PIXELS, save a downscaled copy and return its path.
    Otherwise return the original path unchanged.
    """
    w, h = _ffprobe_size(video_path)
    if not w or not h:
        log(f"  ⚠ לא הצלחתי לקרוא רזולוציה של {video_path.name} — מעלה כמו שזה")
        return video_path
    pixels = w * h
    log(f"  📐 רזולוציה: {w}×{h} ({pixels:,} פיקסלים)")
    if pixels <= MAX_PIXELS:
        return video_path

    # Need to downscale — preserve aspect ratio, fit within MAX_PIXELS
    import math
    scale = math.sqrt(MAX_PIXELS / pixels)
    new_w = int(w * scale)
    new_h = int(h * scale)
    # Round to even (ffmpeg requirement)
    new_w -= new_w % 2
    new_h -= new_h % 2
    log(f"  ✂️ מקטין ל-{new_w}×{new_h} ({new_w * new_h:,} פיקסלים)")

    out_path = video_path.parent / f"_scaled_{video_path.stem}_{new_w}x{new_h}.mp4"
    ffmpeg = _ffmpeg_bin()
    if not ffmpeg:
        log("  ⚠ ffmpeg לא זמין — מעלה את הוידאו המקורי (BytePlus עלול לדחות)")
        return video_path
    try:
        result = subprocess.run(
            [
                ffmpeg, "-y", "-i", str(video_path),
                "-vf", f"scale={new_w}:{new_h}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "copy",
                str(out_path),
            ],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            log(f"  ⚠ ffmpeg downscale failed: {result.stderr[-300:]}")
            return video_path
        log(f"  ✓ נשמר: {out_path.name}")
        return out_path
    except Exception as e:
        log(f"  ⚠ downscale exception: {e}")
        return video_path


def get_ref_video_urls(log=print):
    """Upload (or reuse cached) reference video URLs. Returns list[str]."""
    paths = st.session_state.get("ref_video_paths", []) or []
    if not paths:
        return []

    if _upload_video is None:
        log("⚠ upload_video module not available — skipping reference videos")
        return []

    # Cache uploaded URLs per file path so we don't re-upload the same file
    cache = st.session_state.setdefault("_ref_video_url_cache", {})
    urls = []
    for p in paths[:3]:  # BytePlus max 3 reference videos
        if p in cache:
            urls.append(cache[p])
            continue
        try:
            log(f"📤 מכין וידאו רפרנס: {Path(p).name}")
            # Downscale if pixel count > BytePlus limit
            scaled_path = _downscale_if_needed(Path(p), log=log)
            log(f"📤 מעלה לקטבוקס: {scaled_path.name}")
            url = _upload_video(scaled_path)
            cache[p] = url
            urls.append(url)
        except Exception as e:
            log(f"⚠ שגיאה בהעלאת {Path(p).name}: {e}")
    return urls
