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
        "🎙 Voice generation mode (Seed Audio 1.0) — voiceover / dialogue / reference voice",
        value=False,
        key="audio_mode_toggle",
        help="Switches to the voice generation screen. Uncheck to return to the video screen.",
    )


def maybe_render_audio_studio(project_root) -> bool:
    is_audio = render_audio_mode_toggle()
    if is_audio:
        render_audio_studio(Path(project_root))
    return is_audio


def render_audio_studio(project_root: Path) -> None:
    st.header("🎙 Seed Audio 1.0 — Voice Generation")
    st.caption(
        "Next-gen TTS: voiceover, multi-character dialogue, emotion, background music and effects — "
        "from a single prompt. You can download the voice or use it as reference audio for Seedance."
    )
    st.info(
        "🌐 **Languages:** officially **English + Chinese** (per the docs — more languages "
        "are expected by the end of July). Hebrew is not official yet — we still send it to try; "
        "if the quality is poor, write in English or use a dedicated Hebrew TTS.",
        icon="ℹ️",
    )
    st.caption("💰 Pricing per the docs: ~$0.15 per minute of generated audio.")

    prompt = st.text_area(
        "Prompt: scene/voice description + the text to be read",
        height=200,
        key="audio_prompt",
        placeholder=(
            "English with a rich description is recommended. Example:\n"
            "A sunlit kitchen, soft morning ambience. A warm female narrator, "
            "calm and confident, says: 'This tiny ring tracks your sleep and "
            "never needs charging.'"
        ),
    )
    n = len(prompt)
    st.caption(f"{n} / 2048 characters" + ("  ⚠️ over the limit" if n > 2048 else ""))

    c1, c2 = st.columns(2)
    with c1:
        fmt = st.selectbox("Format", ["mp3", "wav", "ogg_opus", "pcm"], index=0, key="audio_fmt")
    with c2:
        sample_rate = st.selectbox("Sample rate", [24000, 48000, 44100, 32000, 16000, 8000],
                                   index=0, format_func=lambda x: f"{x/1000:g}kHz", key="audio_sr")

    c3, c4, c5 = st.columns(3)
    with c3:
        speech_rate = st.slider("Speech rate", -50, 100, 0, 5, key="audio_speed",
                                help="0 = normal, 100 = double speed, -50 = half")
    with c4:
        loudness_rate = st.slider("Loudness", -50, 100, 0, 5, key="audio_loud",
                                  help="0 = normal, 100 = double, -50 = half")
    with c5:
        pitch_rate = st.slider("Pitch", -12, 12, 0, 1, key="audio_pitch",
                               help="semitones, -12..12")

    st.markdown("**🎧 Reference audio for voice cloning (optional — up to 3, each ≤30 seconds)**")
    st.caption(
        "Upload a voice clip (mp3/wav) and the model will mimic its timbre. In the prompt, refer to them as "
        "@Audio1 / @Audio2 / @Audio3. Reference audio and reference images cannot be combined."
    )
    ref_files = st.file_uploader(
        "Up to 3 audio files",
        type=["mp3", "wav", "ogg", "pcm"],
        accept_multiple_files=True,
        key="audio_ref_uploader",
    )

    if st.button("🎙 Generate voice", type="primary", key="audio_generate_btn"):
        if not prompt.strip():
            st.warning("Write a prompt first.")
            st.stop()
        if n > 2048:
            st.warning("The prompt is too long (2048 characters max).")
            st.stop()

        # Reference audio → base64 (audio_data), sent straight to the API.
        # No external upload needed — far more reliable on Streamlit Cloud
        # than catbox (which is blocked from datacenter IPs).
        references = None
        if ref_files:
            import base64 as _b64
            refs = []
            with st.status("Preparing reference audio...", expanded=True) as up:
                for uf in ref_files[:3]:
                    raw = uf.getvalue()
                    if len(raw) > 10 * 1024 * 1024:
                        up.write(f"⚠️ {uf.name} is over 10MB — skipped (limit: 10MB / 30 seconds).")
                        continue
                    refs.append({"audio_data": _b64.b64encode(raw).decode()})
                    up.write(f"✓ {uf.name} ready")
                up.update(label="Reference audio ready", state="complete")
            references = refs or None
        out_dir = project_root / "outputs" / "audio"
        ext = "ogg" if fmt == "ogg_opus" else fmt
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"voice_{ts}.{ext}"

        try:
            with st.status("Generating voice with Seed Audio 1.0...", expanded=True) as status:
                path, data = generate_audio(
                    prompt.strip(), out_path,
                    references=references or None,
                    fmt=fmt, sample_rate=sample_rate,
                    speech_rate=speech_rate, loudness_rate=loudness_rate,
                    pitch_rate=pitch_rate, log=status.write,
                )
                status.update(label="✅ Voice ready", state="complete")

            st.success(f"✅ Saved: {path.name}"
                       + (f"  ·  {data['duration']}s" if data.get("duration") else ""))
            st.audio(str(path))
            with open(path, "rb") as f:
                st.download_button("⬇ Download voice", f, file_name=path.name, key="audio_dl")

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
                    "🔗 The voice was published as a URL and is available as reference audio for Seedance. "
                    "Turn off voice mode and return to the video screen to use it.", icon="🔗",
                )
                st.code(stable_url, language=None)
        except Exception as exc:
            st.error(f"❌ {exc}")
            st.caption(
                "Check that SEED_AUDIO_API_KEY is set in .env (the X-Api-Key from the "
                "Voice console) and that the 'Dola_SeedSpeech_Seed_Audio_V1' service is enabled."
            )

    st.markdown("---")
    st.caption("⬆ Uncheck 'Voice generation mode' above to return to the video screen.")
