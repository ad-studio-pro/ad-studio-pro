"""
Seed Audio 1.0 generator (CLI) — BytePlus Voice console.

Needs SEED_AUDIO_API_KEY in .env (X-Api-Key from the Voice console; the service
"Dola_SeedSpeech_Seed_Audio_V1" must be activated).

Examples:
    # Text-to-audio (T2A) — describe voice/scene + the line to say
    python scripts/generate_audio.py \
      "Warm female narrator, calm and confident: 'This ring tracks your sleep.'" \
      --name vo --format mp3

    # Try Hebrew (English+Chinese officially; Hebrew is unofficial — test it)
    python scripts/generate_audio.py "קריין חם ובטוח: 'הטבעת עוקבת אחרי השינה שלך.'" --name vo_he

    # Voice cloning from a reference clip (public URL), tagged @Audio1 in the text
    python scripts/generate_audio.py \
      "@Audio1 as the narrator: 'Welcome to the store.'" \
      --ref-audio https://your-bucket.com/voice.mp3 --name testimonial
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seed_audio_client import generate_audio, build_references

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "audio"
LOGS_DIR = PROJECT_ROOT / "outputs" / "logs"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("text_prompt", help="Voice/scene description + text to synthesize (<=2048 chars)")
    p.add_argument("--name", default="audio", help="Output basename")
    p.add_argument("--ref-audio", action="append", default=[],
                   help="Reference audio: public URL or voice/speaker id. Up to 3. Tag @Audio1.. in text.")
    p.add_argument("--ref-image", default=None,
                   help="Reference image URL (mutually exclusive with --ref-audio).")
    p.add_argument("--format", default="mp3", choices=["mp3", "wav", "pcm", "ogg_opus"])
    p.add_argument("--sample-rate", type=int, default=24000,
                   choices=[8000, 16000, 24000, 32000, 44100, 48000])
    p.add_argument("--speech-rate", type=int, default=0, help="-50..100 (0=normal, 100=2x, -50=0.5x)")
    p.add_argument("--loudness-rate", type=int, default=0, help="-50..100")
    p.add_argument("--pitch-rate", type=int, default=0, help="-12..12 semitones")
    args = p.parse_args()

    references = build_references(audio=args.ref_audio or None, image=args.ref_image)

    ext = "ogg" if args.format == "ogg_opus" else args.format
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"{args.name}_{ts}.{ext}"

    path, data = generate_audio(
        args.text_prompt, output_path,
        references=references or None,
        fmt=args.format, sample_rate=args.sample_rate,
        speech_rate=args.speech_rate, loudness_rate=args.loudness_rate,
        pitch_rate=args.pitch_rate,
    )

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    (LOGS_DIR / f"audio_{args.name}_{ts}.json").write_text(json.dumps({
        "name": args.name, "timestamp": datetime.now().isoformat(),
        "text_prompt": args.text_prompt, "references": references,
        "result": data, "output_file": str(path),
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[DONE] Audio: {path}")
    if data.get("url"):
        print(f"[URL ] Temp URL (~2h): {data['url']}")


if __name__ == "__main__":
    main()
