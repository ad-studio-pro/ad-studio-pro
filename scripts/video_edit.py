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
from upload_image import upload_image


def edit_video(source_video_path, instruction, out_path, *,
               image_paths=None, extra_video_paths=None,
               ratio="9:16", duration=None, resolution="720p",
               generate_audio=True, extend=False, log=print):
    """Edit or extend an existing video via Seedance 2.5 V2V.

    instruction: what to change (edit) or what happens next (extend).
                 Reference uploads with @Video 1 (the source), @Video 2.. (extra
                 clips) and @Image 1.. (reference images) — exactly like the
                 official Seedance 2.5 UI. Example instruction:
                 "change the shirt in @Video 1 to the jacket in @Image 1".
    image_paths: reference images (product / clothing / background) → @Image 1..N
    extra_video_paths: extra reference clips → @Video 2..N
    duration: output seconds (4-30 for 2.5).
    Returns the local Path of the new clip.
    """
    source_video_path = Path(source_video_path)
    if not source_video_path.exists():
        raise FileNotFoundError(source_video_path)

    log(f"📤 Uploading source video (@Video 1): {source_video_path.name}")
    src_url = upload_video(source_video_path)
    video_urls = [src_url]

    # Extra reference videos → @Video 2, @Video 3 (Seedance allows up to 3 total)
    for i, vp in enumerate(list(extra_video_paths or [])[:2], start=2):
        if Path(vp).exists():
            log(f"📤 Uploading reference video (@Video {i}): {Path(vp).name}")
            video_urls.append(upload_video(Path(vp)))

    # Reference images → @Image 1.. (up to 9)
    image_urls = []
    for i, ip in enumerate(list(image_paths or [])[:9], start=1):
        if Path(ip).exists():
            log(f"📤 Uploading reference image (@Image {i}): {Path(ip).name}")
            image_urls.append(upload_image(Path(ip)))

    _refs_note = ""
    if image_urls:
        _refs_note += f" You may reference @Image 1..{len(image_urls)}."
    if len(video_urls) > 1:
        _refs_note += f" You may reference @Video 2..{len(video_urls)}."

    if extend:
        prompt = (f"Continue from the last frame of @Video 1 without any visible "
                  f"cut. {instruction} Keep the same subject, style, lighting and "
                  f"camera language as @Video 1.{_refs_note}")
    else:
        prompt = (f"Edit the video @Video 1: {instruction} Keep everything else "
                  f"identical — same subject, same motion, same camera movement, "
                  f"same background, same lighting and timing as @Video 1. Change "
                  f"ONLY what is described.{_refs_note} No on-screen text, no captions.")

    dur = int(duration) if duration else 5
    dur = max(4, min(dur, 30))

    log(f"📨 Sending V2V ({'extend' if extend else 'edit'}) to Seedance 2.5 "
        f"({resolution}, {ratio}, {dur}s · {len(video_urls)} video / {len(image_urls)} image refs)...")
    task_id = submit_task(
        prompt=prompt,
        model=model_for_engine("2.5"),
        image_urls=image_urls or None,
        video_urls=video_urls,
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
