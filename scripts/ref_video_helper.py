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


def _ffprobe_size(video_path):
    """Return (width, height) of the video, or (None, None) on failure."""
    ffmpeg = _ffmpeg_bin()
    if not ffmpeg:
        return None, None
    try:
        result = subprocess.run(
            [ffmpeg, "-i", str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
        stderr = result.stderr
        import re
        m = re.search(r"\s(\d{3,5})x(\d{3,5})[,\s]", stderr)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return None, None


def _downscale_if_needed(video_path, log=print):
    """If the video exceeds MAX_PIXELS, save a downscaled copy and return its path.
    Otherwise return the original path unchanged.
    """
    w, h = _ffprobe_size(video_path)
    if not w or not h:
        log(f"  ⚠ לא הצלחתי לקרוא רזולוציה של {Path(video_path).name} — מעלה כמו שזה")
        return video_path
    pixels = w * h
    log(f"  📐 רזולוציה: {w}×{h} ({pixels:,} פיקסלים)")
    if pixels <= MAX_PIXELS:
        return video_path

    import math
    scale = math.sqrt(MAX_PIXELS / pixels)
    new_w = int(w * scale)
    new_h = int(h * scale)
    new_w -= new_w % 2
    new_h -= new_h % 2
    log(f"  ✂️ מקטין ל-{new_w}×{new_h} ({new_w * new_h:,} פיקסלים)")

    out_path = Path(video_path).parent / f"_scaled_{Path(video_path).stem}_{new_w}x{new_h}.mp4"
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


def _blur_faces_in_video(video_path, log=print):
    """Detect faces in each frame and apply heavy Gaussian blur to those regions.
    Passes Seedance's InputVideoSensitiveContentDetected filter while preserving
    motion/composition/style.

    Returns Path to blurred H.264 mp4 if faces were detected and processing
    succeeded; otherwise returns the original path unchanged.
    """
    video_path = Path(video_path)
    try:
        import cv2
    except ImportError:
        log("  ⚠ opencv-python-headless לא מותקן — מדלג על טשטוש פנים")
        return video_path

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        log("  ⚠ לא הצלחתי לטעון את ה-Haar cascade — מדלג על טשטוש פנים")
        return video_path

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        log(f"  ⚠ לא הצלחתי לפתוח את {video_path.name} — מדלג על טשטוש")
        return video_path

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    raw_path = video_path.parent / f"_blur_raw_{video_path.stem}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(raw_path), fourcc, fps, (width, height))
    if not out.isOpened():
        log("  ⚠ לא הצלחתי לפתוח קובץ פלט לטשטוש — מדלג")
        cap.release()
        return video_path

    total_face_frames = 0
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4,
            minSize=(max(30, width // 20), max(30, height // 20)),
        )
        if len(faces) > 0:
            total_face_frames += 1
            for (x, y, w, h) in faces:
                pad_x = int(w * 0.25)
                pad_top = int(h * 0.40)
                pad_bot = int(h * 0.20)
                x0 = max(0, x - pad_x)
                y0 = max(0, y - pad_top)
                x1 = min(width, x + w + pad_x)
                y1 = min(height, y + h + pad_bot)
                roi = frame[y0:y1, x0:x1]
                if roi.size > 0:
                    kw = max(31, (x1 - x0) // 4) | 1
                    kh = max(31, (y1 - y0) // 4) | 1
                    blurred = cv2.GaussianBlur(roi, (kw, kh), 30)
                    frame[y0:y1, x0:x1] = blurred
        out.write(frame)

    cap.release()
    out.release()

    if total_face_frames == 0:
        log("  ℹ לא זוהו פנים בוידאו — מעלה את המקור")
        raw_path.unlink(missing_ok=True)
        return video_path

    log(f"  🫥 טושטשו פנים ב-{total_face_frames}/{frame_count} פריימים")

    ffmpeg = _ffmpeg_bin()
    if not ffmpeg:
        log("  ⚠ ffmpeg לא זמין — מעלה בקודק mp4v (יתכן ש-Seedance ידחה)")
        return raw_path
    final_path = video_path.parent / f"_blurred_{video_path.stem}.mp4"
    try:
        result = subprocess.run(
            [ffmpeg, "-y", "-i", str(raw_path),
             "-c:v", "libx264", "-preset", "fast", "-crf", "23",
             "-pix_fmt", "yuv420p",
             "-an",
             str(final_path)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            log(f"  ✓ קודד מחדש ל-H.264: {final_path.name}")
            raw_path.unlink(missing_ok=True)
            return final_path
        log(f"  ⚠ ffmpeg re-encode failed: {result.stderr[-300:]}")
    except Exception as e:
        log(f"  ⚠ ffmpeg re-encode exception: {e}")
    return raw_path


def get_ref_video_urls(log=print):
    """Upload (or reuse cached) reference video URLs. Returns list[str].

    Honors st.session_state['ex_blur_faces'] (default True) for automatic
    face blurring.
    """
    paths = st.session_state.get("ref_video_paths", []) or []
    if not paths:
        return []

    if _upload_video is None:
        log("⚠ upload_video module not available — skipping reference videos")
        return []

    blur_enabled = st.session_state.get("ex_blur_faces", True)

    cache = st.session_state.setdefault("_ref_video_url_cache", {})
    urls = []
    for p in paths[:3]:
        if p in cache:
            urls.append(cache[p])
            continue
        try:
            log(f"📤 מכין וידאו רפרנס: {Path(p).name}")
            current = Path(p)
            # Step 1: Auto-blur faces
            if blur_enabled:
                log("  🫥 בודק פנים בוידאו ומטשטש אם נמצאו...")
                current = _blur_faces_in_video(current, log=log)
            # Step 2: Downscale if too big
            current = _downscale_if_needed(current, log=log)
            # Step 3: Upload
            log(f"📤 מעלה לקטבוקס: {current.name}")
            url = _upload_video(current)
            cache[p] = url
            urls.append(url)
        except Exception as e:
            log(f"⚠ שגיאה בהעלאת {Path(p).name}: {e}")
    return urls
