"""
Reference video helper — uploads user-uploaded reference videos to catbox
and caches the URLs. Stage 4 uses these as `video_urls` in submit_task.

Pipeline order (each step is optional / falls back to passthrough on failure):
  1. Auto-blur faces  — passes Seedance InputVideoSensitiveContentDetected filter
  2. Auto-downscale   — BytePlus rejects videos > ~2.08M pixels (~1080p)
  3. Upload to catbox — with tmpfiles.org fallback
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


def _blur_faces_in_video(video_path: Path, log=print) -> Path:
    """Detect faces in each frame and apply heavy Gaussian blur to those regions.
    This passes Seedance's InputVideoSensitiveContentDetected filter while
    preserving everything else about the video (motion, composition, style).

    Pipeline:
      1. OpenCV reads frames one at a time
      2. Haar cascade detects faces
      3. Each detected region gets a heavy Gaussian blur (with 30% padding on top
         for forehead/hair)
      4. Frames written to a temp mp4v video
      5. ffmpeg re-encodes to H.264 (Seedance requires H.264, not mp4v)

    Returns:
        Path to blurred H.264 mp4 if faces were detected and processing succeeded.
        Otherwise returns the original path unchanged.
    """
    try:
        import cv2  # opencv-python-headless
    except ImportError:
        log("  ⚠ opencv-python-headless לא מותקן — מדלג על טשטוש פנים")
        return video_path

    cascade_path = cv2.data.haarcascades + "h