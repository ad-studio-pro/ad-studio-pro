"""
Full-pipeline smoke test using BytePlus's own public demo assets.

Why: lets us verify auth + model + reference handling + polling + download
WITHOUT needing imgbb or any image-hosting setup.

Run:  python scripts/test_full_pipeline.py
"""

from pathlib import Path
from datetime import datetime

from byteplus_client import (
    submit_task, poll_task, download_video, extract_video_url,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "videos"

# Public BytePlus demo assets (from the official console example)
DEMO_PROMPT = (
    "Use the first-person POV framing from Video 1 throughout, and use "
    "Audio 1 as the background music throughout. First-person POV fruit "
    "tea promotional ad; opening frame is Image 1, your hand picks a "
    "dew-covered red apple. 2-4 seconds: fast cuts, your hand drops apple "
    "chunks into a shaker, adds ice and tea base, shakes forcefully. "
    "4-6 seconds: first-person close-up of the finished drink, layered "
    "fruit tea is poured into a clear cup. 6-8 seconds: first-person "
    "hand-held toast shot, you raise the fruit tea from Image 2 toward "
    "the camera, the final frame freezes on Image 2."
)

DEMO_IMAGES = [
    "https://ark-doc.tos-ap-southeast-1.bytepluses.com/doc_image/r2v_tea_pic1.jpg",
    "https://ark-doc.tos-ap-southeast-1.bytepluses.com/doc_image/r2v_tea_pic2.jpg",
]
DEMO_VIDEOS = [
    "https://ark-doc.tos-ap-southeast-1.bytepluses.com/doc_video/r2v_tea_video1.mp4",
]
DEMO_AUDIOS = [
    "https://ark-doc.tos-ap-southeast-1.bytepluses.com/doc_audio/r2v_tea_audio1.mp3",
]


def main():
    print("=" * 60)
    print("BytePlus full-pipeline smoke test")
    print("=" * 60)

    task_id = submit_task(
        prompt=DEMO_PROMPT,
        image_urls=DEMO_IMAGES,
        video_urls=DEMO_VIDEOS,
        audio_urls=DEMO_AUDIOS,
        ratio="16:9",
        duration=11,
        generate_audio=True,
        watermark=False,
    )

    result = poll_task(task_id)
    video_url = extract_video_url(result)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"_smoke_test_{timestamp}.mp4"
    download_video(video_url, output_path)

    print(f"\n[DONE] Smoke test passed. Video: {output_path}")


if __name__ == "__main__":
    main()
