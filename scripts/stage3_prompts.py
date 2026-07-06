"""
Stage 3 — Seedance 2.0 Prompt Generation (per video row)

Inputs:  Stage 2 plan JSON, the skill files
Outputs: per-video prompt populated into the plan, plus a human-readable MD

For each video row in plan["videos"]:
  - Look up family (A/B/C/D)
  - Pick the matching structure template from structures.md
  - Pick format-specific concept seeds from format-catalog.md
  - Apply category-specific physical rules + negatives
  - Generate the prompt via Claude.ai (CDP)
  - Populate row["prompt"]
"""

import os
import json
import re
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CDP_PORT = int(os.getenv("CDP_PORT", "9224"))

MULTI_PRODUCT_RULES = """  VARIANT-SET PROTOCOL (research-based, from the official Seedance 2.0 manual patterns):
  1. Each @Image is ONE separate variant (color/angle/component). NEVER merge variants, NEVER show a multi-pack as one object, NEVER invent colors that have no reference image.
  2. Rotation beats: give each variant its own timestamped beat with a different camera angle/distance. Every beat that shows a product MUST name its exact @Image number.
  3. Anchor repeatedly: reference each @Image at the exact moment it appears on screen AND once in the global consistency line — Seedance needs the mid-timeline reminder, not just a mention at the top.
  4. One-at-a-time rule: only ONE variant visible at any moment; the previous variant is fully removed off-screen before the next appears. Anchor the wear/hold location ONCE (e.g. her LEFT index finger / his LEFT hand) and never move it between beats.
  5. Optional finale: the last beat may show all variants together — if so, write \"all {n} variants from @Image 1 through @Image {n} laid out in a row, each matching its own source image exactly\".
  6. Time budget: ~2s hook + at least 2s per variant + ~2s close. If the duration cannot fit all variants at 2s each, show FEWER variants rather than rushing beats.
  7. Negatives to append: no duplicate products, no merged colors, no variant worn on two places at once, no extra invented variants."""

SKILL_DIR = PROJECT_ROOT / "skills" / "seedance-campaign-factory"


def load_structure_for_family(family: str) -> str:
    """Load Structure A/B/C/D content from structures.md."""
    full = (SKILL_DIR / "references" / "structures.md").read_text(encoding="utf-8")

    # The file is sectioned with "# Structure A — ", "# Structure B — ", etc.
    pattern = rf"# Structure {family} —[\s\S]*?(?=\n# Structure [A-Z]|\n## Multi-Chunk Handling|$)"
    m = re.search(pattern, full)
    if not m:
        # Fallback: return everything
        return full
    return m.group(0)


def load_format_details(format_number: int) -> str:
    """Pull the ## Format N section from format-catalog.md."""
    full = (SKILL_DIR / "references" / "format-catalog.md").read_text(encoding="utf-8")
    pattern = rf"## Format {format_number} —[\s\S]*?(?=\n## Format |\n# Family |\Z)"
    m = re.search(pattern, full)
    return m.group(0) if m else ""


def build_per_video_message(video_row: dict, product_info: dict,
                              structure_text: str, format_text: str,
                              n_images: int = 1, image_roles: list = None) -> str:
    """Build the user message to Claude for ONE video prompt.

    image_roles: optional list of user-provided role labels per image
    (e.g. ["bottle - front", "measuring scoop", "box - back"]) aligned
    with Image 1..N. Injected so Claude assigns each reference correctly.
    """
    # Optional role map — tells Claude what each reference image IS
    role_map_block = ""
    if image_roles and any((r or "").strip() for r in image_roles):
        role_lines = "\n".join(
            f"    @Image {i+1} = {r.strip()}"
            for i, r in enumerate(image_roles) if (r or "").strip()
        )
        role_map_block = (
            "\n  IMAGE ROLE MAP (user-provided — use each reference ONLY for its designated role):\n"
            f"{role_lines}\n"
            "  When a beat shows a specific component/variant, reference its exact @Image number per this map."
        )

    # Build a multi-image directive based on how many references are attached
    if n_images > 1:
        multi_image_block = (
            f"- MULTI-IMAGE REFERENCES ({n_images} images attached): The user uploaded {n_images} distinct product references "
            f"(Image 1, Image 2, ... Image {n_images}). USE MULTIPLE references in different beats — show variety across cuts.\n"
            f"  Example: [00:00] she holds @Image 1 ... [00:05] cut to @Image 3 on her finger ... [00:10] @Image 5 next to @Image 2 on the counter.\n"
            f"  Each beat that shows the product should reference a SPECIFIC image number from 1 to {n_images}.\n"
            f"  Include a consistency anchor: \"All product references @Image 1 through @Image {n_images} must remain visually unchanged across cuts — same colors, materials, shapes as in their respective source images.\"\n"
            f"  NEVER write \"a pack of {n_images} rings\" as if Image 1 contains all of them — each image is one variant/angle, treat them as separate references."
            + role_map_block
            + "\n" + MULTI_PRODUCT_RULES.replace("{n}", str(n_images))
        )
    else:
        multi_image_block = (
            "- Include the @Image 1 consistency anchor line: \"The product from @Image 1 must remain visually unchanged across all cuts — same label, same color, same orientation.\""
        )

    return f"""STAGE 3 TASK: Write ONE Seedance 2.0 video prompt for this row.

PRODUCT:
```json
{json.dumps(product_info, indent=2, ensure_ascii=False)}
```

VIDEO ROW (from the plan):
```json
{json.dumps(video_row, indent=2, ensure_ascii=False)}
```

FORMAT-SPECIFIC DETAILS (Format {video_row.get('format_number')} — {video_row.get('format_name')}):
{format_text}

PROMPT STRUCTURE TO USE (Structure {video_row.get('family')}):
{structure_text}

YOUR TASK:
Write the COMPLETE Seedance 2.0 prompt using the structure above. Follow the template exactly.

REQUIREMENTS:
- Use only the cinematic vocabulary allowed for this family (Structure A: NEVER cinematic, Structure B/C/D: cinematic is encouraged).
{multi_image_block}
- Add the negative block with category-specific negatives (jewelry → no second ring; beverage → no competitor bottle; etc.).
- Word count target — A: 100-260, B: 120-300, C: 180-350, D: 150-280.
- All in English.

OUTPUT: ONE fenced code block containing the prompt. NO commentary. NO preamble. JUST the block."""


def parse_prompt_from_response(response: str) -> str:
    """Extract the prompt from a fenced code block in Claude's response."""
    parts = response.split("```")
    for i, p in enumerate(parts):
        if i % 2 == 1 and p.strip():
            first, _, rest = p.partition("\n")
            if first and len(first) < 20 and " " not in first.strip():
                return rest.strip()
            return p.strip()
    # Fallback: whole response
    return response.strip()


def save_prompts_files(plan: dict, brand_slug: str, output_dir: Path = None) -> tuple:
    """Save the populated plan as JSON + a human-readable MD."""
    if output_dir is None:
        output_dir = PROJECT_ROOT / "outputs" / "prompts"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"{brand_slug}_prompts_{timestamp}.json"
    md_path = output_dir / f"{brand_slug}_prompts_{timestamp}.md"

    json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    # Build Markdown grouped by family → format
    md_parts = [f"# {plan.get('campaign_name', 'Campaign')} — Seedance 2.0 Prompts\n"]

    by_family = {}
    for v in plan.get("videos", []):
        fam = v.get("family", "?")
        fmt = v.get("format_name", "?")
        by_family.setdefault(fam, {}).setdefault(fmt, []).append(v)

    for fam_letter in ["A", "B", "C", "D"]:
        if fam_letter not in by_family:
            continue
        fam_name = {"A": "UGC", "B": "Hero/Premium", "C": "Cinematic",
                    "D": "Pattern Interrupt"}[fam_letter]
        md_parts.append(f"\n## Family {fam_letter} — {fam_name}\n")

        for fmt_name, videos in by_family[fam_letter].items():
            md_parts.append(f"\n### {fmt_name} ({len(videos)} videos)\n")
            for v in videos:
                md_parts.append(f"\n#### {v.get('id')} — {v.get('scene_summary', '')[:80]}")
                md_parts.append(f"- Duration: {v.get('duration_seconds')}s · "
                                f"Aspect: {v.get('aspect_ratio')} · "
                                f"Audio: {'ON' if v.get('generate_audio') else 'OFF'}")
                md_parts.append(f"- Date: {v.get('scheduled_date', '')}")
                md_parts.append("")
                md_parts.append("```")
                md_parts.append(v.get("prompt", "(prompt missing)"))
                md_parts.append("```")
                md_parts.append("\n---\n")

    md_path.write_text("\n".join(md_parts), encoding="utf-8")
    return json_path, md_path


if __name__ == "__main__":
    print("Stage 3 utilities loaded.")
    print(f"  Structure A available: {bool(load_structure_for_family('A'))}")
    print(f"  Format 1 details: {bool(load_format_details(1))}")
