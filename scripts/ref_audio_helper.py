"""
Reference audio helper — connects audio to Seedance 2.0 videos.

Two sources, merged (max 3 refs, MP3, total <=15s per Seedance 2.0 limits):
  1. Voice created in Audio Studio (st.session_state["seed_audio_url"]) —
     used when the user ticks "use as reference audio".
  2. MP3 files uploaded in the Stage-4 UI (music for beat-sync, VO, etc.) —
     uploaded to catbox (tmpfiles fallback) and cached.

Stage 4 passes the returned URLs to submit_task(audio_urls=...), which sends
them as role=reference_audio. In the prompt, refer to them as @Audio 1/2/3
("cuts synchronized to the beat of @Audio 1", "she speaks the words of @Audio 1").
"""

import re
import time
from pathlib import Path

import requests
import streamlit as st

MAX_AUDIO_REFS = 3


def _safe_filename(name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    base = re.sub(r"_+", "_", base).strip("_")
    if not base or "." not in base:
        base = f"audio_{int(time.time())}.mp3"
    return base


def _upload_audio(path: Path) -> str:
    """Upload an MP3 to catbox.moe; tmpfiles.org fallback. Returns public URL."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    safe_name = _safe_filename(path.name)

    last_error = None
    for attempt in range(2):
        try:
            with open(path, "rb") as f:
                resp = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": (safe_name, f, "audio/mpeg")},
                    timeout=180,
                )
                resp.raise_for_status()
                url = resp.text.strip()
                if not url.startswith("http"):
                    raise RuntimeError(f"catbox unexpected: {url}")
                return url
        except Exception as e:
            last_error = e
            time.sleep(1)

    # tmpfiles fallback
    with open(path, "rb") as f:
        resp = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": (safe_name, f, "audio/mpeg")},
            timeout=180,
        )
        resp.raise_for_status()
        raw = resp.json().get("data", {}).get("url", "")
        if not raw:
            raise RuntimeError(f"both hosts failed. catbox: {last_error}")
        return raw.replace("tmpfiles.org/", "tmpfiles.org/dl/")


def get_ref_audio_urls(log=print):
    """Return up to 3 public MP3 URLs to send as reference_audio."""
    urls = []

    # 1. Voice from Audio Studio
    if st.session_state.get("use_seed_audio_ref") and st.session_state.get("seed_audio_url"):
        urls.append(st.session_state["seed_audio_url"])
        log("🎙 מוסיף את הקול מ-Audio Studio כ-@Audio 1")

    # 2. Uploaded MP3s
    paths = st.session_state.get("ref_audio_paths", []) or []
    cache = st.session_state.setdefault("_ref_audio_url_cache", {})
    for p in paths:
        if len(urls) >= MAX_AUDIO_REFS:
            break
        if p in cache:
            urls.append(cache[p])
            continue
        try:
            log(f"📤 מעלה רפרנס אודיו: {Path(p).name}")
            url = _upload_audio(Path(p))
            cache[p] = url
            urls.append(url)
            log(f"  ✓ {url}")
        except Exception as e:
            log(f"⚠ שגיאה בהעלאת {Path(p).name}: {e}")

    return urls[:MAX_AUDIO_REFS]


def render_ref_audio_ui(project_root: Path) -> None:
    """Stage-4 UI block: attach reference audio to the generated videos.
    Shared by Express and Full pipeline (rendered above the generate button).
    """
    with st.expander("🎵 רפרנס אודיו לוידאו (אופציונלי — עד 3 MP3, סה\"כ ≤15 שניות)", expanded=False):
        st.caption(
            "האודיו נשלח לסידנס כ-reference_audio. בפרומט הפנה אליו עם "
            "**@Audio 1** — למשל: *\"cuts synchronized to the beat of @Audio 1\"* "
            "(מוזיקה) או *\"the narrator speaks the voiceover from @Audio 1\"* (קריינות)."
        )

        # Voice from Audio Studio
        seed_url = st.session_state.get("seed_audio_url")
        if seed_url:
            st.checkbox(
                "🎙 השתמש בקול שיצרת ב-Audio Studio כ-@Audio 1",
                value=st.session_state.get("use_seed_audio_ref", True),
                key="use_seed_audio_ref",
            )
            st.code(seed_url, language=None)
        else:
            st.caption("💡 טיפ: צור קריינות ב'מצב יצירת קול' למעלה — היא תופיע כאן אוטומטית.")

        files = st.file_uploader(
            "קבצי MP3 (מוזיקה / קריינות / אפקטים)",
            type=["mp3"],
            accept_multiple_files=True,
            key="ref_audio_uploader",
        )
        if files:
            audio_dir = Path(project_root) / "assets" / "ref_audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            paths = []
            for uf in files[:MAX_AUDIO_REFS]:
                p = audio_dir / uf.name
                p.write_bytes(uf.getvalue())
                paths.append(str(p))
                st.audio(str(p))
            st.session_state["ref_audio_paths"] = paths
            st.success(f"✓ {len(paths)} קבצי אודיו מוכנים — יועלו בזמן הייצור וישלחו כ-reference_audio.")
        else:
            st.session_state.pop("ref_audio_paths", None)
