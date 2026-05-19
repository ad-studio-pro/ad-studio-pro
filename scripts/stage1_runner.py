"""
Stage 1 Runner — full Stage 1 orchestration.

Flow:
  1. Gemini Vision auto-detects product
  2. Tavily fetches live trend research
  3. Claude.ai composes the viral content brief from raw research
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stage1_research import detect_product, research_trends
import prompt_generator as pg
from language_rule import ENGLISH_DIALOGUE_RULE


def run_stage1(image_path: Path, total_videos: int = 5,
                duration: int = 10,
                audience_override: str = "American",
                user_notes: str = "",
                log=print) -> dict:
    """Returns: {product, trends, viral_brief}"""
    log("─── Stage 1A: Product detection (Gemini Vision) ───")
    product = detect_product(image_path)
    log(f"  ✓ Category: {product.get('category')}")
    log(f"  ✓ Niche: {product.get('niche_keyword')}")
    log(f"  ✓ Auto-detected audience: {product.get('audience_default')}")

    # HARD override: user's UI choice always wins
    if audience_override:
        product["audience_default"] = audience_override
        # Also override region cue so the Claude brief stays consistent
        AUDIENCE_TO_REGION = {
            "American": "global",
            "Israeli": "IL",
            "Pan-Arab / MENA": "MENA",
            "Slavic / CIS": "CIS",
            "East Asian": "CN",
            "Latin American": "LatAm",
            "Mixed international": "global",
        }
        product["region_cue"] = AUDIENCE_TO_REGION.get(audience_override, "global")
        log(f"  → AUDIENCE OVERRIDE: {audience_override} (user choice in UI)")
    log("")

    log("─── Stage 1B: Trend research (Tavily, 8 queries) ───")
    trends = research_trends(product.get("niche_keyword", "product"), log=log)
    log(f"  ✓ {sum(len(q['results']) for q in trends['queries'])} sources gathered")
    log("")

    log("─── Stage 1C: Viral Brief composition (Claude.ai) ───")
    brief_message = f"""You are arcads-prompts skill. Compose the VIRAL CONTENT BRIEF for Stage 1.

PRODUCT DETECTED:
```json
{json.dumps(product, indent=2, ensure_ascii=False)}
```

LIVE TREND RESEARCH (from Tavily, this week):
```json
{json.dumps(trends, indent=2, ensure_ascii=False)[:8000]}
```

SCALE: Generate exactly {total_videos} video idea(s) — adapt detail level:
  - 1-5 videos: detailed brief per video, very specific scenes
  - 6-20 videos: lean brief, focused on variation
  - 21-100+: high-level mix, varied across formats

{ENGLISH_DIALOGUE_RULE}

TASK: Compose a brief covering:
1. **Trends table** — what's winning this week in this niche (3-7 rows)
2. **Competitor patterns** — what brands are doing (3-5 patterns)
3. **Hook patterns** — verbal/visual hooks that work (5-10 hooks)
4. **Recommended Content Mix** — per-format counts as a CONSEQUENCE of the trends, framed as: "Based on what's moving this week..." Format: "8 challenge-style UGC · 8 sidewalk interviews · 7 honest reviews · ..."
5. **EXACTLY {total_videos} seed idea(s)** distributed across formats. For small batches (1-5), make each idea highly specific and detailed. For large batches, vary aggressively.

For every seed idea, include:
```
N. **[Title]**
- Format: [name from format-catalog.md]
- Family: [A/B/C/D]
- Duration: [N] seconds
- Aspect ratio: 9:16 (default)
- Setting: [specific]
- Persona: [age, gender, heritage, vibe]
- Scene: [≤2 sentences]
- Hook line: [the verbal/visual hook]
- Inspired by: [trend from research]
- Why viral now: [reason]
```

OUTPUT: Markdown formatted brief. No JSON fence around the whole thing. Sections clearly separated. Hebrew comments OK in section names if helpful."""

    brief = pg.call_claude_ai(brief_message, log=log)

    return {"product": product, "trends": trends, "viral_brief": brief}


if __name__ == "__main__":
    print("Stage 1 runner — call run_stage1(image_path) from the app.")

def recommend_formats_from_research(stage1_result: dict, total_videos: int,
                                       enabled_format_pool: list,
                                       user_notes: str = "",
                                       log=print) -> dict:
    """
    Use Claude.ai to pick the best formats for THIS product/research,
    rather than relying on a generic priority list.

    Returns: {format_number: count, ...} totaling exactly total_videos.
    """
    from stage2_plan import ALL_FORMATS

    # Build a compact catalog of available formats with vibes
    catalog_lines = []
    for fmt_num in enabled_format_pool:
        slug, family, display = ALL_FORMATS[fmt_num]
        catalog_lines.append(f"  {fmt_num}. [Family {family}] {display}")
    catalog = chr(10).join(catalog_lines)

    product = stage1_result.get("product", {})
    brief = stage1_result.get("viral_brief", "")

    notes_block = ("USER NOTES:" + chr(10) + user_notes + chr(10) + chr(10)) if user_notes else ""
    n_formats = len(enabled_format_pool)
    product_json = __import__("json").dumps(product, indent=2, ensure_ascii=False)

    message = f"""SMART FORMAT SELECTION — pick the optimal mix for THIS product, based on research.

PRODUCT:
```json
{product_json}
```

VIRAL CONTENT BRIEF (already researched):
{brief}

{notes_block}AVAILABLE FORMATS (you may pick from these only):
{catalog}

TASK: Distribute exactly {total_videos} videos across the formats that will perform BEST for THIS specific product, audience, and current trends. Use the research's "Recommended Content Mix" as your starting point — but adjust based on what makes sense for the product and the available format list above.

OUTPUT: Return ONLY a JSON object — no markdown fences, no commentary:

{{
  "selections": [
    {{"format_number": 3, "count": 2, "rationale": "research shows reviews convert best for this niche"}},
    {{"format_number": 5, "count": 2, "rationale": "ASMR is trending this week for pain relief content"}},
    {{"format_number": 1, "count": 1, "rationale": "entertainment format builds awareness"}}
  ]
}}

Counts MUST sum to exactly {total_videos}. Use 1-{n_formats} distinct formats."""

    log(f"  🤖 Asking Claude to pick optimal formats from research...")
    response = pg.call_claude_ai(message, log=log)

    # Multi-strategy JSON parsing (Claude sometimes adds prose / smart quotes / trailing commas)
    import json, re
    parsed = None
    raw = response.strip()

    # Strategy 1: try the whole response
    try:
        parsed = json.loads(raw)
    except Exception:
        pass

    # Strategy 2: find content inside ```json ... ``` fences
    if parsed is None:
        m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
        if m:
            try:
                parsed = json.loads(m.group(1))
            except Exception:
                pass

    # Strategy 3: find the outermost {...}
    if parsed is None:
        first = raw.find("{")
        last = raw.rfind("}")
        if first >= 0 and last > first:
            candidate = raw[first:last + 1]
            # Clean common issues: smart quotes, trailing commas
            cleaned = (candidate
                       .replace("\u201c", "\"").replace("\u201d", "\"")
                       .replace("\u2018", "'").replace("\u2019", "'"))
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            try:
                parsed = json.loads(cleaned)
            except Exception as e:
                # Strategy 4: extract just the "selections" array via regex
                m2 = re.search(r'"selections"\s*:\s*(\[[\s\S]*?\])', cleaned)
                if m2:
                    try:
                        arr = json.loads(m2.group(1))
                        parsed = {"selections": arr}
                    except Exception:
                        pass

    if parsed is None:
        log(f"  ⚠ Could not parse JSON. Raw response (first 600 chars):")
        log(f"     {raw[:600]}")
        raise RuntimeError(f"Smart Pick parsing failed. Response sample: {raw[:200]}")
    selections = parsed.get("selections", [])
    split = {}
    for sel in selections:
        fn = int(sel["format_number"])
        cnt = int(sel["count"])
        if fn in enabled_format_pool and cnt > 0:
            split[fn] = split.get(fn, 0) + cnt
            log(f"    ✓ Format {fn}: ×{cnt} — {sel.get('rationale', '')[:60]}")

    # Sanity: if total is off, scale to total_videos
    actual = sum(split.values())
    if actual != total_videos and actual > 0:
        # Simple proportional rescale
        scaled = {k: max(1, round(v * total_videos / actual)) for k, v in split.items()}
        log(f"    [scale] Claude returned {actual}, scaling to {total_videos}: {scaled}")
        split = scaled

    return split

