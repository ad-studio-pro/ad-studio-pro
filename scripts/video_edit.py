"""
Video editing (Seedance 2.5 V2V) — edit a video you already generated.

Two operations, same ARK endpoint + key as generation:
  • edit   — upload a source video + describe a change ("replace the gun with a
             book", "remove the logo on the wall", "change the shirt to blue").
             The subject/motion/camera are kept; only what you describe changes.
  • extend — continue the clip past its last frame ("he then walks off-screen").

Requires Seedance 2.5 (30s single-take, R2V/V2V editing). The source video is
uploaded (catbox → tmpfiles fallback) and passed as reference_video; the model
returns a NEW edited clip.
"""

from pathlib import Path

from byteplus_client import (submit_task, poll_task, download_video,
                             extract_video_url, model_for_engine)
from upload_video import upload_video


def edit_video(source_video_path, instruction, out_path, *,
               ratio="9:16", duration=None, resolution="720p",
               generate_audio=True, extend=False, log=print):
    """Edit or extend an existing video via Seedance 2.5 V2V.

    instruction: what to change (edit) or what happens next (extend).
    duration: output seconds (defaults to source-ish; 4-30 for 2.5).
    Returns the local Path of the new clip.
    """
    source_video_path = Path(source_video_path)
    if not source_video_path.exists():
        raise FileNotFoundError(source_video_path)

    log(f"📤 Uploading source video: {source_video_path.name}")
    src_url = upload_video(source_video_path)

    if extend:
        prompt = (f"Continue from the last frame of @Video 1 without any visible "
                  f"cut. {instruction} Keep the same subject, style, lighting and "
                  f"camera language as @Video 1.")
    else:
        prompt = (f"Edit the video @Video 1: {instruction} Keep everything else "
                  f"identical — same subject, same motion, same camera movement, "
                  f"same background, same lighting and timing as @Video 1. Change "
                  f"ONLY what is described. No on-screen text, no captions.")

    dur = int(duration) if duration else 5
    dur = max(4, min(dur, 30))

    log(f"📨 Sending V2V ({'extend' if extend else 'edit'}) to Seedance 2.5 "
        f"({resolution}, {ratio}, {dur}s)...")
    task_id = submit_task(
        prompt=prompt,
        model=model_for_engine("2.5"),
        video_urls=[src_url],
        ratio=ratio,
        duration=dur,
        generate_audio=generate_audio,
        watermark=False,
        extra_payload={"resolution": resolution},
    )
    log(f"  task_id: {task_id}")
    result = poll_task(task_id, log=log)
    url = extract_video_url(result)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    download_video(url, out_path)
    log(f"  ✅ {out_path.name}")
    return out_path
