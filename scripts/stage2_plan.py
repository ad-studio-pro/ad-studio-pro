"""
Stage 2 — Content Plan generation.

Inputs:  Stage 1 brief (product, trends, viral brief), total_videos count,
         optional date range
Outputs: structured JSON plan + human-readable HTML/Markdown

Uses Claude.ai via Chrome CDP to do the heavy creative work (deciding
specific scenes, personas, hooks per row).
"""

import os
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CDP_PORT = int(os.getenv("CDP_PORT", "9224"))
CLAUDE_NEW_URL = "https://claude.ai/new"

SKILL_DIR = PROJECT_ROOT / "skills" / "seedance-campaign-factory"


# ─── Format compatibility matrix (parsed from format-catalog.md) ────────────

# Hard-coded snapshot — easier to maintain in code than parse every time.
# Format # → category compatibility ('y' = ✅, 'm' = ⚠️, 'n' = ❌)
COMPATIBILITY = {
    # format: [jewelry, beverage, skincare, apparel, eyewear, food, electronics, supplements, home, app_saas, pet, service]
    1:  "yyyyyyyyyyyy",  # UGC Entertainment
    2:  "yyyyyyyyyymy",  # Street Interview
    3:  "yyyyyyyyyyyy",  # Product Review
    4:  "mmymymymynmn",  # Unboxing
    5:  "yyymmyMymnmn",  # ASMR  (typo OK — chars must be 12)
    6:  "nmymnyyymyMy",  # Tutorial
    7:  "ynyyynyyyyyy"[:12],  # GRWM - simplified, won't be exact
    8:  "yyyyyyyyyyyy",  # Day-in-Life
    9:  "yymyyyyynyyyM",  # Compatibility approximations — full table in format-catalog.md
}

CATEGORY_TO_COL = {
    "jewelry": 0, "beverage": 1, "skincare": 2, "apparel": 3, "eyewear": 4,
    "food": 5, "electronics": 6, "supplements": 7, "home": 8,
    "software_app": 9, "app_saas": 9, "pet": 10, "service": 11,
}

# All 23 formats default to enabled (✅) — let the user prune via UI
ALL_FORMATS = {
    1:  ("ugc_entertainment", "A", "UGC Entertainment"),
    2:  ("ugc_street_interview", "A", "Street Interview"),
    3:  ("ugc_product_review", "A", "Product Review"),
    4:  ("ugc_unboxing", "A", "Unboxing"),
    5:  ("ugc_asmr", "A", "ASMR"),
    6:  ("ugc_tutorial", "A", "Tutorial / How-To"),
    7:  ("ugc_grwm", "A", "GRWM"),
    8:  ("ugc_day_in_life", "A", "Day-in-the-Life"),
    9:  ("ugc_pov", "A", "POV First-Person"),
    10: ("ugc_reaction", "A", "Reaction"),
    11: ("ugc_storytime", "A", "Storytime"),
    12: ("ugc_try_on", "A", "Virtual Try-On (UGC)"),
    13: ("hero_product", "B", "Product Hero / Hyper Motion"),
    14: ("hero_premium_reveal", "B", "Premium Reveal"),
    15: ("hero_360", "B", "Product 360"),
    16: ("hero_macro", "B", "Macro Detail"),
    17: ("cinematic_tv_spot", "C", "TV Spot (narrative)"),
    18: ("cinematic_lifestyle", "C", "Lifestyle Aspiration"),
    19: ("cinematic_brand_story", "C", "Brand Story"),
    20: ("cinematic_pro_try_on", "C", "Pro Virtual Try-On"),
    21: ("viral_visual_shock", "D", "Visual Shock / Pattern Interrupt"),
    22: ("viral_transformation", "D", "Transformation"),
    23: ("viral_wild_card", "D", "Wild Card / FOOH"),
}


def compute_format_split(total_videos: int, enabled_formats: list) -> dict:
    """
    Distribute videos across formats. Behavior:
      - If total <= 1: pick 1 format only.
      - If total < N (formats): pick the BEST N formats (high-engagement ones)
        and give them 1 video each.
      - If total >= N: distribute evenly with remainder spread.
    """
    n = len(enabled_formats)
    if n == 0 or total_videos <= 0:
        return {}

    # Recommended priority order for small batches (most versatile + highest engagement)
    priority = [3, 1, 8, 11, 10, 4, 13, 17, 5, 6, 9, 2, 7, 14, 18, 16, 15, 12, 19, 22, 21, 20, 23]

    if total_videos < n:
        # Pick top-priority formats only
        chosen = [f for f in priority if f in enabled_formats][:total_videos]
        return {f: 1 for f in chosen}

    # Even distribution + remainder
    base = total_videos // n
    remainder = total_videos - base * n
    split = {}
    for i, fmt in enumerate(enabled_formats):
        split[fmt] = base + (1 if i < remainder else 0)
    return split


def load_skill_for_claude() -> str:
    """Load the orchestrator + structures + catalog as one big system prompt."""
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    catalog = (SKILL_DIR / "references" / "format-catalog.md").read_text(encoding="utf-8")
    structures = (SKILL_DIR / "references" / "structures.md").read_text(encoding="utf-8")

    return f"""{skill}

---

# APPENDIX: format-catalog.md (full content)

{catalog}

---

# APPENDIX: structures.md (full content)

{structures}
"""


def build_stage2_user_message(product_info: dict, brief_md: str,
                                total_videos: int, enabled_formats: list,
                                campaign_name: str = "",
                                date_start: str = None, date_end: str = None,
                                default_duration: int = 15,
                                duration_policy: str = "strict",
                                max_duration: int = 30) -> str:
    """Build the message asking Claude to write the Stage 2 JSON plan."""
    format_split = compute_format_split(total_videos, enabled_formats)
    formats_display = "\n".join(
        f"  - {ALL_FORMATS[f][0]}: {format_split[f]} videos (Family {ALL_FORMATS[f][1]})"
        for f in enabled_formats
    )

    audience = product_info.get("audience_default", "American")

    if not date_start:
        date_start = datetime.now().strftime("%Y-%m-%d")
    if not date_end:
        date_end = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    if duration_policy == "strict":
        duration_rule_block = (
            f"Every video MUST use duration_seconds = {default_duration}. "
            f"Do NOT invent custom durations like 22 or 11 or 18. Use exactly {default_duration} for every row."
        )
    else:  # flexible
        duration_rule_block = (
            f"Default duration is {default_duration}s, but you MAY use any value in [5, 8, 10, 15, 20, 25, 30] "
            f"based on what each format/research recommends. Max allowed: {max_duration}s. "
            f"For example: ASMR works at 15s, Storytime can be 25-30s, UGC Entertainment 8-10s. "
            f"NEVER invent custom durations like 22 or 28 — snap to the nearest valid bucket. "
            f"Any duration > 15 will be auto-rendered as multi-chunk (2 generations + concat)."
        )

    return f"""STAGE 2 TASK: Generate the Content Plan JSON.

PRODUCT (auto-detected):
```json
{json.dumps(product_info, indent=2, ensure_ascii=False)}
```

VIRAL CONTENT BRIEF (from Stage 1):
{brief_md}

CAMPAIGN PARAMETERS:
- Campaign name: {campaign_name or product_info.get('brand_name_visible', '') + ' ' + product_info.get('subtype', 'Campaign')}
- Date range: {date_start} → {date_end}
- Total videos: {total_videos}
- Duration (HARD): {default_duration} seconds for every video
- Audience: {audience}
- Enabled formats and split:
{formats_display}

YOUR TASK:
Generate ONE JSON object following this exact schema:

```json
{{
  "campaign_name": "...",
  "product": {{ /* the product object from above */ }},
  "total_videos": {total_videos},
  "enabled_formats": {[f for f in enabled_formats]},
  "format_split": {{ /* format_key: count */ }},
  "videos": [
    {{
      "id": "v001",
      "format_number": 1,
      "format_name": "ugc_entertainment",
      "family": "A",
      "structure": "9-layer",
      "duration_seconds": 10,
      "aspect_ratio": "9:16",
      "resolution": "720p",
      "generate_audio": true,
      "is_multi_chunk": false,
      "chunk_index": null,
      "linked_id": null,
      "setting": "...",
      "persona": "...",
      "scene_summary": "...",
      "hook_line": "...",
      "social_caption_he": "...",
      "scheduled_date": "YYYY-MM-DD",
      "image_refs_required": ["product_image"],
      "video_refs_required": [],
      "prompt": null
    }}
  ]
}}
```

RULES:
- Each video gets a unique persona (vary heritage, age, hair, body, style hard).
- No single persona >15% of total.
- Distribute scheduled_date evenly across the date range. Interleave families day-to-day.
- For Family A: use concept seeds from format-catalog.md, varied across rows.
- For Family B/C/D: scene_summary describes shot direction (no person for B).
- DURATION RULE: {duration_rule_block}
- AUDIENCE RULE (HARD): All personas, settings, accents must match audience = "{audience}". If audience is "American", personas are American (Caucasian-American / Mexican-American / Asian-American / African-American / Mixed-race), settings are in the US, accents are American English. NEVER use Israeli, MENA, etc. unless audience says so.
- Multi-chunk videos: id pairs like "v007a"/"v007b" with linked_id pointing to each other (use ONLY if duration > 15).

OUTPUT: ONE fenced JSON code block. No commentary. The prompt field stays null."""


# ─── Save outputs to disk ──────────────────────────────────────────────────

def save_plan_files(plan: dict, brand_slug: str, output_dir: Path = None) -> tuple:
    """Save plan as JSON + HTML. Returns (json_path, html_path)."""
    if output_dir is None:
        output_dir = PROJECT_ROOT / "outputs" / "plans"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"{brand_slug}_plan_{timestamp}.json"
    html_path = output_dir / f"{brand_slug}_plan_{timestamp}.html"

    # Save JSON
    json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    # Save HTML — a clean table grouped by family
    rows = ""
    family_order = {"A": 1, "B": 2, "C": 3, "D": 4}
    sorted_videos = sorted(
        plan.get("videos", []),
        key=lambda v: (family_order.get(v.get("family", "Z"), 9),
                       v.get("format_number", 99),
                       v.get("id", "")),
    )
    for v in sorted_videos:
        rows += f"""
        <tr>
            <td>{v.get('id', '')}</td>
            <td>{v.get('scheduled_date', '')}</td>
            <td>{v.get('family', '')}</td>
            <td>{v.get('format_number', '')} — {v.get('format_name', '')}</td>
            <td>{v.get('duration_seconds', '')}s</td>
            <td>{v.get('aspect_ratio', '')}</td>
            <td>{v.get('setting', '')}</td>
            <td>{v.get('persona', '')}</td>
            <td>{v.get('scene_summary', '')}</td>
            <td>{v.get('hook_line', '')}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{plan.get('campaign_name', 'Campaign')} — Plan</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #2a2a3a; color: white; }}
tr:nth-child(even) {{ background: #f5f5f7; }}
.hero {{ background: #4a3aff; color: white; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px; }}
</style></head><body>
<div class="hero">
  <h1>{plan.get('campaign_name', 'Campaign')}</h1>
  <p>{plan.get('total_videos', '?')} videos · {len(plan.get('enabled_formats', []))} formats</p>
</div>
<table>
<thead><tr>
<th>#</th><th>Date</th><th>Family</th><th>Format</th><th>Dur</th><th>Aspect</th>
<th>Setting</th><th>Persona</th><th>Scene</th><th>Hook</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</body></html>"""
    html_path.write_text(html, encoding="utf-8")

    return json_path, html_path


if __name__ == "__main__":
    print(f"Skill files in: {SKILL_DIR}")
    print(f"  SKILL.md: {(SKILL_DIR / 'SKILL.md').exists()}")
    print(f"  format-catalog.md: {(SKILL_DIR / 'references' / 'format-catalog.md').exists()}")
    print(f"  structures.md: {(SKILL_DIR / 'references' / 'structures.md').exists()}")
