"""
Reference video helper — uploads user-uploaded reference videos to catbox
and caches the URLs. Stage 4 uses these as `video_urls` in submit_task.

Used as:
    from ref_video_helper import get_ref_video_urls
    refs = get_ref_video_urls(log=s4_status.write)  # returns list[str]
    # pass `refs` as video_urls in submit_task

If the user didn't upload reference videos, returns [] (no-op).
"""

from pathlib import Path
import streamlit as st

try:
    from upload_video import upload_video as _upload_video
except Exception:
    _upload_video = None


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
            log(f"📤 מעלה וידאו רפרנס לקטבוקס: {Path(p).name}")
            url = _upload_video(Path(p))
            cache[p] = url
            urls.append(url)
        except Exception as e:
            log(f"⚠ שגיאה בהעלאת {Path(p).name}: {e}")
    return urls
