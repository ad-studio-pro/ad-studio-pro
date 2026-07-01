"""
BytePlus Seed Audio 1.0 client — voice / audio generation (non-streaming TTS).

Based on the official "BytePlus Seed Audio 1.0 HTTP API Integration Guide".
This is a SEPARATE service from Seedance/ModelArk:

  Activate:  BytePlus Voice console -> service "Dola_SeedSpeech_Seed_Audio_V1"
             https://console.byteplus.com/voice/new/setting/activate
  Endpoint:  POST https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/create
  Auth:      header  X-Api-Key: <key from the Voice/Speech console>   (recommended)
             legacy  X-Api-App-Id + X-Api-Access-Key
  Style:     SYNCHRONOUS — one POST returns the audio (base64 + temp url), no polling.
  Limits:    text_prompt <= 2048 chars; output <= 120s; up to 3 audio refs
             (<=30s / <=10MB each); 1 image ref; audio & image refs cannot mix.
  Languages: English + Chinese today (more "coming by end of July" per the docs).
             Hebrew is NOT officially supported yet — we send it anyway to test.

Config (env / Streamlit secrets):
  SEED_AUDIO_API_KEY     X-Api-Key from the Voice console. Falls back to
                         ARK_API_KEY (same key as Seedance) if unset.
  SEED_AUDIO_URL         default https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/create
  SEED_AUDIO_MODEL_ID    default seed-audio-1.0
  SEED_AUDIO_APP_ID      (legacy auth) X-Api-App-Id
  SEED_AUDIO_ACCESS_KEY  (legacy auth) X-Api-Access-Key
"""

import os
import uuid
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

try:
    import streamlit as st
    _SECRETS = dict(st.secrets) if hasattr(st, "secrets") else {}
except Exception:
    _SECRETS = {}

DEFAULT_URL = "https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/create"
DEFAULT_MODEL = "seed-audio-1.0"  # BytePlus Voice / Seed Speech console

_FORMATS = ("wav", "mp3", "pcm", "ogg_opus")
_SAMPLE_RATES = (8000, 16000, 24000, 32000, 44100, 48000)


def _get(key, default=""):
    val = os.getenv(key)
    if val:
        return val
    return _SECRETS.get(key, default)


def _url():
    return _get("SEED_AUDIO_URL", DEFAULT_URL)


def _model_id():
    return _get("SEED_AUDIO_MODEL_ID", DEFAULT_MODEL)


def _headers():
    """Build auth headers. Prefer the new single-header X-Api-Key mode;
    fall back to legacy App-Id + Access-Key if those are set instead."""
    h = {"Content-Type": "application/json",
         "X-Api-Request-Id": str(uuid.uuid4())}

    app_id = _get("SEED_AUDIO_APP_ID")
    access_key = _get("SEED_AUDIO_ACCESS_KEY")
    api_key = _get("SEED_AUDIO_API_KEY") or _get("ARK_API_KEY")

    if app_id and access_key:                      # legacy two-header mode
        h["X-Api-App-Id"] = app_id
        h["X-Api-Access-Key"] = access_key
    elif api_key:                                  # new single-header mode
        h["X-Api-Key"] = api_key
    else:
        raise RuntimeError(
            "No Seed Audio credentials. Set SEED_AUDIO_API_KEY (X-Api-Key from "
            "the BytePlus Voice console) in .env / Streamlit secrets — or reuse "
            "ARK_API_KEY, or the legacy SEED_AUDIO_APP_ID + SEED_AUDIO_ACCESS_KEY."
        )
    return h


def build_references(audio=None, image=None):
    """Turn simple inputs into the API's references array.

    audio: list of str. 'http...' -> {audio_url}; else treated as a voice/
           speaker id -> {speaker}. (Base64 clips: pass {"audio_data": b64}
           dicts directly instead of a string.)
    image: single str. 'http...' -> {image_url}; else base64 -> {image_data}.
    Audio and image references cannot be combined.
    """
    if audio and image:
        raise ValueError("Audio and image references cannot be mixed.")
    refs = []
    for item in (audio or [])[:3]:
        if isinstance(item, dict):
            refs.append(item)
        elif isinstance(item, str) and item.startswith("http"):
            refs.append({"audio_url": item})
        else:
            refs.append({"speaker": item})
    if image:
        img = image[0] if isinstance(image, (list, tuple)) else image
        if isinstance(img, dict):
            refs.append(img)
        elif isinstance(img, str) and img.startswith("http"):
            refs.append({"image_url": img})
        else:
            refs.append({"image_data": img})
    return refs


def generate_audio(text_prompt, output_path, *, references=None,
                   fmt="mp3", sample_rate=24000,
                   speech_rate=0, loudness_rate=0, pitch_rate=0,
                   model=None, timeout=120, log=print):
    """Synchronous generate. Writes the audio file. Returns (path, data).

    Rates follow the docs: speech_rate/loudness_rate are ints -50..100
    (0 = normal, 100 = 2.0x, -50 = 0.5x); pitch_rate is -12..12 semitones.
    'data' includes the temporary 'url' (valid ~2h) usable as a Seedance
    reference_audio, plus 'duration' / 'original_duration'.
    """
    if len(text_prompt) > 2048:
        raise ValueError(f"text_prompt is {len(text_prompt)} chars (max 2048).")
    if fmt not in _FORMATS:
        raise ValueError(f"format must be one of {_FORMATS}")
    if sample_rate not in _SAMPLE_RATES:
        raise ValueError(f"sample_rate must be one of {_SAMPLE_RATES}")

    payload = {
        "model": model or _model_id(),
        "text_prompt": text_prompt,
        "audio_config": {
            "format": fmt,
            "sample_rate": sample_rate,
            "speech_rate": int(speech_rate),
            "loudness_rate": int(loudness_rate),
            "pitch_rate": int(pitch_rate),
        },
        "watermark": {},
    }
    if references:
        payload["references"] = references

    log(f"   \U0001F399 sending Seed Audio request ({len(text_prompt)} chars)...")
    resp = requests.post(_url(), json=payload, headers=_headers(), timeout=timeout)

    if resp.status_code >= 400:
        body = resp.text or ""
        low = body.lower()
        if "voiceprint" in low or "clone" in low or "sensitive" in low:
            raise RuntimeError(
                "Seed Audio blocked this for a sensitive voice / voice-clone "
                "reason. Simplify the voice description and avoid real people.\n\n"
                f"source: {body[:400]}"
            )
        raise RuntimeError(f"Seed Audio failed [{resp.status_code}]: {body}")

    data = resp.json()
    code = data.get("code")
    if code not in (0, None, 200, "0"):
        raise RuntimeError(f"Seed Audio error code={code}: {data.get('message')}\n{data}")

    b64 = data.get("audio")
    if not b64:
        raise RuntimeError(f"No 'audio' in response. Keys: {list(data.keys())}\n{data}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(b64))
    dur = data.get("duration")
    log(f"   ✅ saved {output_path.name}  ({output_path.stat().st_size/1024:.0f} KB"
        + (f", {dur}s)" if dur else ")"))
    data.pop("audio", None)
    return output_path, data


def test_connection():
    """One tiny synchronous request to verify credentials + endpoint + model."""
    key = _get("SEED_AUDIO_API_KEY") or _get("ARK_API_KEY")
    masked = (key[:6] + "..." + key[-4:]) if key else "(missing)"
    print(f"URL     : {_url()}")
    print(f"Model   : {_model_id()}")
    print(f"X-Api-Key: {masked}"
          + ("  (from ARK_API_KEY fallback)" if not _get('SEED_AUDIO_API_KEY') else ""))
    print()
    out = PROJECT_ROOT / "outputs" / "audio" / "connection_test.mp3"
    try:
        path, data = generate_audio(
            "This is a short connection test for Seed Audio one point zero.",
            out, fmt="mp3",
        )
        print(f"[OK] Works. Saved {path}  meta={data}")
        return path
    except Exception as exc:
        print(f"[FAIL] {exc}")
        print("\nTIP: activate 'Dola_SeedSpeech_Seed_Audio_V1' in the BytePlus "
              "Voice console and set SEED_AUDIO_API_KEY to that console's API key.")
        raise


if __name__ == "__main__":
    test_connection()
