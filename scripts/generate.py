"""
ThunderFit ad generator — Seedance 2.0 via BytePlus ModelArk.

Usage:
    python scripts/generate.py prompts/01_chef_male.md \
        --image assets/product/ring_male_thunderfit_v1.jpg
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from byteplus_client import (
    submit_task, poll_task, download_video, extract_video_url
)
from upload_image import upload_image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "videos"
LOGS_DIR = PROJECT_ROOT / "outputs" / "logs"


def extract_prompt_text(md_file: Path) -> str:
    """Pull prompt from first ``` block, or whole file if no block."""
    content = md_file.read_text(encoding="utf-8")
    if "```" in content:
        parts = content.split("```")
        if len(parts) >= 3:
            return parts[1].strip()
    return content.strip()


def normalize_image_refs(prompt: str) -> str:
    """
    Convert reference syntax to official BytePlus convention.
    Per the official console sample, refs in text are written as
    "Image 1", "Image 2", "Video 1", "Audio 1".
    """
    for i in range(9, 0, -1):
        prompt = prompt.replace(f"@(img{i})",   f"Image {i}")
        prompt = prompt.replace(f"@image{i}",   f"Image {i}")
        prompt = prompt.replace(f"@(video{i})", f"Video {i}")
        prompt = prompt.replace(f"@video{i}",   f"Video {i}")
        prompt = prompt.replace(f"@(audio{i})", f"Audio {i}")
        prompt = prompt.replace(f"@audio{i}",   f"Audio {i}")
    return prompt


def log_run(name, prompt, task_id, result, output_path):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "name": name,
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "prompt": prompt,
        "result": result,
        "output_file": str(output_path),
    }
    log_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Log -> {log_file}")
    return log_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt_file")
    parser.add_argument("--image", required=True, help="Reference image path")
    parser.add_argument("--name", help="Output basename (default: prompt filename)")
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--ratio", default="9:16")
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--model", default=None, help="Override SEEDANCE_MODEL_ID")
    parser.add_argument("--resolution", default=None, help="Optional. Sent only if provided.")
    args = parser.parse_args()

    prompt_file = Path(args.prompt_file)
    image_file  = Path(args.image)
    name = args.name or prompt_file.stem

    if not prompt_file.exists():
        sys.exit(f"[FAIL] Prompt file not found: {prompt_file}")
    if not image_file.exists():
        sys.exit(f"[FAIL] Image file not found: {image_file}")

    prompt = normalize_image_refs(extract_prompt_text(prompt_file))
    print(f"[..] Prompt loaded ({len(prompt)} chars)")

    image_url = upload_image(image_file)

    extra = {}
    if args.resolution:
        extra["resolution"] = args.resolution

    task_id = submit_task(
        prompt=prompt,
        image_urls=[image_url],
        model=args.model,
        ratio=args.ratio,
        duration=args.duration,
        generate_audio=not args.no_audio,
        watermark=False,
        extra_payload=(extra or None),
    )

    result = poll_task(task_id)

    video_url = extract_video_url(result)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"{name}_{timestamp}.mp4"
    download_video(video_url, output_path)

    log_run(name, prompt, task_id, result, output_path)
    print(f"\n[DONE] Video: {output_path}")


if __name__ == "__main__":
    main()
