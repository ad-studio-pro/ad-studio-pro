"""
Stage 3 Runner — per-video prompt generation.

For each video row in the plan, calls Claude.ai with the right structure
and populates row["prompt"]. Saves JSON + Markdown deliverables.
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stage3_prompts import (
    load_structure_for_family, load_format_details,
    build_per_video_message, parse_prompt_from_response, save_prompts_files,
)
import prompt_generator as pg
from language_rule import ENGLISH_DIALOGUE_RULE


def run_stage3(plan: dict, product: dict,
                image_path: Path = None,
                image_paths: list = None,
                image_roles: list = None,
                limit: int = None,
                user_notes: str = "",
                log=print, progress=None) -> dict:
    """
    Populates each video's `prompt` field. Returns the updated plan.
    Also saves prompts.json and prompts.md.

    Args:
        plan: from run_stage2()
        product: from run_stage1()
        image_path: the product reference image (attached to every call)
        limit: only process first N videos (for testing)
        progress: optional callback(i, total) for UI progress bars
    """
    videos = plan.get("videos", [])
    if limit:
        videos = videos[:limit]

    total = len(videos)
    log(f"─── Stage 3: Writing {total} prompts ───")

    # Cache structures by family (only 4 unique values)
    structure_cache = {}
    format_cache = {}

    for idx, video in enumerate(videos, 1):
        log(f"\n[{idx}/{total}] {video.get('id')} — {video.get('format_name')}...")

        family = video.get("family", "A")
        fmt_num = video.get("format_number", 1)

        if family not in structure_cache:
            structure_cache[family] = load_structure_for_family(family)
        if fmt_num not in format_cache:
            format_cache[fmt_num] = load_format_details(fmt_num)

        n_imgs = len(image_paths) if image_paths else (1 if image_path else 0)
        message = build_per_video_message(
            video, product,
            structure_cache[family],
            format_cache[fmt_num],
            n_images=n_imgs,
            image_roles=image_roles,
        )
        if user_notes:
            message = f"USER NOTES (must reflect in the prompt):\n```\n{user_notes}\n```\n\n" + message
        # ALWAYS inject the English-dialogue rule
        message = ENGLISH_DIALOGUE_RULE + "\n\n" + message

        try:
            attach_list = list(image_paths) if image_paths else ([image_path] if image_path else None)
            response = pg.call_claude_ai(
                message,
                attachments=attach_list,
                log=log,
                max_wait_s=300,
            )
            video["prompt"] = parse_prompt_from_response(response)
            log(f"  ✓ {len(video['prompt'])} chars")
        except Exception as e:
            log(f"  ✗ FAILED: {e}")
            video["prompt"] = f"[GENERATION FAILED: {e}]"

        if progress:
            progress(idx, total)

    # Save deliverables
    brand_slug = (product.get("brand_name_visible", "")
                  .strip().lower().replace(" ", "-") or "campaign")
    json_path, md_path = save_prompts_files(plan, brand_slug)
    log(f"\n✓ Saved: {json_path.name}")
    log(f"✓ Saved: {md_path.name}")

    plan["_files"] = plan.get("_files", {})
    plan["_files"].update({"prompts_json": str(json_path), "prompts_md": str(md_path)})
    return plan


if __name__ == "__main__":
    print("Stage 3 runner — call run_stage3(plan, product, image_path) from the app.")
