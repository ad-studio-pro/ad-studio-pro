"""
Seed Audio 1.0 panel for the Streamlit app (BytePlus Voice — synchronous TTS).

app.py calls:
    from audio_studio import maybe_render_audio_studio
    if maybe_render_audio_studio(PROJECT_ROOT):
        st.stop()          # voice mode takes over the page

Generates a voice/audio clip, lets the user play + download it, and (via catbox)
publishes a stable URL saved to st.session_state["seed_audio_url"] so it can be
reused as reference_audio for a Seedance video.
"""

from pathlib import Path
from datetime import datetime
import streamlit as st

from seed_audio_client import generate_audio, build_references

try:
    from upload_video import upload_video_to_catbox as _upload_to_catbox
except Exception:
    _upload_to_catbox = None


def render_audio_mode_toggle() -> bool:
    return st.checkbox(
        "🎙 מצב יצירת קול (Seed Audio 1.0) — קריינות / דיאלוג / קול לרפרנס",
        value=False,
        key="audio_mode_toggle",
        help="עובר למסך יצירת קול. בטל את הסימון כדי לחזור למסך הווידאו.",
    )


def maybe_render_audio_studio(project_root) -> bool:
    is_audio = render_audio_mode_toggle()
    if is_audio:
        render_audio_studio(Path(project_root))
    return is_audio


def render_audio_studio(project_root: Path) -> None:
    st.header("🎙 Seed Audio 1.0 — יצירת קול")
    st.caption(
        "TTS מהדור הבא: קריינות, דיאלוג רב-דמויות, רגש, מוזיקת רקע ואפקטים — "
        "מפרומט אחד. אפשר להוריד את הקול או להשתמש בו כרפרנס-אודיו לסידנס."
    )
    st.info(
        "🌐 **שפות:** רשמית **אנגלית + סינית** (לפי הדוקומנטציה — שפות נוספות "
        "אמורות להגיע סוף יולי). עברית עדיין לא רשמית — שולחים בכל זאת כדי לבדוק; "
        "אם האיכות לא טובה, כדאי לכתוב באנגלית או להשתמש ב-TTS ייעודי לעברית.",
        icon="ℹ️",
    )
    st.caption("💰 תמחור לפי הדוקומנטציה: ~0.15$ לדקת אודיו שנוצרת.")

    prompt = st.text_area(
        "פרומט: תיאור הסצנה/הקול + הטקסט להקראה",
        height=200,
        key="audio_prompt",
        placeholder=(
            "מומלץ אנגלית + תיאור עשיר. דוגמה:\n"
            "A sunlit kitchen, soft morning ambience. A warm female narrator, "
            "calm and confident, says: 'This tiny ring tracks your sleep and "
            "never needs charging.'"
        ),
    )
    n = len(prompt)
    st.caption(f"{n} / 2048 תווים" + ("  ⚠️ חורג מהמקסימום" if n > 2048 else ""))

    c1, c2 = st.columns(2)
    with c1:
        fmt = st.selectbox("פורמט", ["mp3", "wav", "ogg_opus", "pcm"], index=0, key="audio_fmt")
    with c2:
        sample_rate = st.selectbox("Sample rate", [24000, 48000, 44100, 32000, 16000, 8000],
                                   index=0, format_func=lambda x: f"{x/1000:g}kHz", key="audio_sr")

    c3, c4, c5 = st.columns(3)
    with c3:
        speech_rate = st.slider("מהירות דיבור", -50, 100, 0, 5, key="audio_speed",
                                help="0 = רגיל, 100 = מהירות כפולה, -50 = חצי")
    with c4:
        loudness_rate = st.slider("עוצמה", -50, 100, 0, 5, key="audio_loud",
                                  help="0 = רגיל, 100 = כפול, -50 = חצי")
    with c5:
        pitch_rate = st.slider("גובה קול", -12, 12, 0, 1, key="audio_pitch",
                               help="semitones, -12..12")

    st.markdown("**🎧 רפרנס-אודיו לשכפול קול (אופציונלי — עד 3, כל אחד ≤30 שניות)**")
    st.caption(
        "העלה קליפ קול (mp3/wav) והמודל יחקה את הטמבר. בפרומט הפנה אליהם עם "
        "@Audio1 / @Audio2 / @Audio3. רפרנס-אודיו ורפרנס-תמונה לא יכולים לבוא יחד."
    )
    ref_files = st.file_uploader(
        "עד 3 קבצי אודיו",
        type=["mp3", "wav", "ogg", "pcm"],
        accept_multiple_files=True,
        key="audio_ref_uploader",
    )

    if st.button("🎙 צור קול", type="primary", key="audio_generate_btn"):
        if not prompt.strip():
            st.warning("כתוב פרומט קודם.")
            st.stop()
        if n > 2048:
            st.warning("הפרומט ארוך מדי (מקסימום 2048 תווים).")
            st.stop()

        audio_urls = []
        if ref_files:
            if _upload_to_catbox is None:
                st.error("אין רכיב העלאה זמין לרפרנס-אודיו.")
                st.stop()
            ref_dir = project_root / "assets" / "ref_audio"
            ref_dir.mkdir(parents=True, exist_ok=True)
            with st.status("מעלה רפרנס-אודיו...", expanded=True) as up:
                for uf in ref_files[:3]:
                    local = ref_dir / uf.name
                    local.write_bytes(uf.getvalue())
                    url = _upload_to_catbox(local)
                    audio_urls.append(url)
                    up.write(f"✓ {uf.name} → {url}")
                up.update(label="רפרנס-אודיו מוכן", state="complete")

        references = build_references(audio=audio_urls or None)
        out_dir = project_root / "outputs" / "audio"
        ext = "ogg" if fmt == "ogg_opus" else fmt
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"voice_{ts}.{ext}"

        try:
            with st.status("יוצר קול עם Seed Audio 1.0...", expanded=True) as status:
                path, data = generate_audio(
                    prompt.strip(), out_path,
                    references=references or None,
                    fmt=fmt, sample_rate=sample_rate,
                    speech_rate=speech_rate, loudness_rate=loudness_rate,
                    pitch_rate=pitch_rate, log=status.write,
                )
                status.update(label="✅ הקול מוכן", state="complete")

            st.success(f"✅ נשמר: {path.name}"
                       + (f"  ·  {data['duration']}s" if data.get("duration") else ""))
            st.audio(str(path))
            with open(path, "rb") as f:
                st.download_button("⬇ הורד קול", f, file_name=path.name, key="audio_dl")

            # Publish a stable URL for reuse as a Seedance reference_audio.
            stable_url = data.get("url")
            if _upload_to_catbox is not None:
                try:
                    stable_url = _upload_to_catbox(path)
                except Exception:
                    pass  # fall back to the temporary (~2h) API url
            if stable_url:
                st.session_state["seed_audio_url"] = stable_url
                st.session_state["seed_audio_path"] = str(path)
                st.info(
                    "🔗 הקול פורסם כ-URL וזמין כרפרנס-אודיו לסידנס. כבה את מצב הקול "
                    "וחזור למסך הווידאו כדי להשתמש בו.", icon="🔗",
                )
                st.code(stable_url, language=None)
        except Exception as exc:
            st.error(f"❌ {exc}")
            st.caption(
                "בדוק ש-SEED_AUDIO_API_KEY מוגדר ב-.env (ה-X-Api-Key מקונסולת "
                "ה-Voice) ושהשירות 'Dola_SeedSpeech_Seed_Audio_V1' מופעל."
            )

    st.markdown("---")
    st.caption("⬆ בטל את הסימון של 'מצב יצירת קול' למעלה כדי לחזור למסך הווידאו.")
