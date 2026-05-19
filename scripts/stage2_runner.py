"""
Stage 2 Runner — Content Plan JSON generation.
Takes Stage 1 output + parameters, asks Claude.ai for full plan JSON.
"""

import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from language_rule import ENGLISH_DIALOGUE_RULE
from stage2_plan import (
    compute_format_split, ALL_FORMATS, build_stage2_user_message, save_plan_files,
)
import prompt_generator as pg


def run_stage2(product: dict, viral_brief: str,
                total_videos: int = 5,
                enabled_formats: list = None,
                campaign_name: str = "",
                date_start: str = None,
                date_end: str = None,
                default_duration: int = 15,
                duration_policy: str = "strict",
                max_duration: int = 30,
                user_notes: str = "",
                n_images: int = 1,
                log=print) -> dict:
    """
    Returns the populated plan dict (also saved to disk).
    """
    if enabled_formats is None:
        # Default: enable all 23
        enabled_formats = list(ALL_FORMATS.keys())

    log("─── Stage 2: Plan generation (Claude.ai) ───")
    log(f"  Total videos: {total_videos}")
    log(f"  Enabled formats: {len(enabled_formats)}")

    message = build_stage2_user_message(
        product, viral_brief, total_videos, enabled_formats,
        campaign_name, date_start, date_end,
        default_duration=default_duration,
        duration_policy=duration_policy,
        max_duration=max_duration,
    )
    if user_notes:
        message = f"USER NOTES (apply throughout the plan):\n```\n{user_notes}\n```\n\n" + message
    # Tell Claude how many images are available
    if n_images > 1:
        image_note = (
            f"IMAGE REFERENCES: The user uploaded {n_images} distinct product images "
            f"(Image 1, Image 2, ... Image {n_images}). Across the campaign, distribute "
            f"these references — different videos may emphasize different images. In each "
            f"video's `image_refs_required` field, list ALL the image refs the prompt will "
            f"actually use (e.g. [\"Image 1\", \"Image 3\"]).\n\n"
        )
        message = image_note + message
    # ALWAYS inject the English-dialogue rule (Seedance language constraint)
    message = ENGLISH_DIALOGUE_RULE + "\n\n" + message

    response = pg.call_claude_ai(message, log=log, max_wait_s=900)

    # Extract the JSON
    plan = _parse_plan_json(response)

    # Post-process duration based on policy
    VALID = [5, 8, 10, 15, 20, 25, 30]
    if "videos" in plan:
        for v in plan["videos"]:
            actual = v.get("duration_seconds", default_duration)
            if duration_policy == "strict":
                if actual != default_duration:
                    log(f"  ⚠ {v.get('id')}: strict mode — {actual}s → {default_duration}s")
                    v["duration_seconds"] = default_duration
            else:  # flexible
                # Snap to nearest valid bucket, respect max_duration
                snapped = min(VALID, key=lambda x: abs(x - actual))
                snapped = min(snapped, max_duration)
                if snapped != actual:
                    log(f"  ✓ {v.get('id')}: flexible — Claude wanted {actual}s, snapped to {snapped}s")
                v["duration_seconds"] = snapped
                v["is_multi_chunk"] = snapped > 15

    # Save
    brand_slug = (product.get("brand_name_visible", "")
                  .strip().lower().replace(" ", "-") or "campaign")
    json_path, html_path = save_plan_files(plan, brand_slug)
    log(f"  ✓ Plan saved: {json_path.name}")
    log(f"  ✓ HTML view: {html_path.name}")

    plan["_files"] = {"json": str(json_path), "html": str(html_path)}
    return plan


def _parse_plan_json(response: str) -> dict:
    """Pull the first {...} JSON object out of Claude's response."""
    # Try fenced first
    parts = response.split("```")
    for i, p in enumerate(parts):
        if i % 2 == 1:
            txt = p.strip()
            if txt.startswith("json"):
                txt = txt[4:].strip()
            if txt.startswith("{"):
                try:
                    return json.loads(txt)
                except json.JSONDecodeError:
                    pass

    # Fallback: scan for the outermost {...}
    first = response.find("{")
    last = response.rfind("}")
    if first >= 0 and last > first:
        try:
            return json.loads(response[first:last + 1])
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Plan JSON parse failed: {e}\n\n{response[:500]}")

    raise RuntimeError(f"No JSON in plan response: {response[:500]}")


if __name__ == "__main__":
    print("Stage 2 runner — call run_stage2(product, viral_brief, ...) from the app.")
