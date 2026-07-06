---
name: seedance-campaign-factory
description: >
  Product-agnostic UGC + Cinematic ad campaign factory for Seedance 2.0.
  Works for any product (rings, beverages, skincare, apparel, electronics,
  food, supplements, pet, app). Auto-detects category from an uploaded image,
  researches what's trending this week (TikTok / Reels / Shorts), then builds
  a plan distributed across 23 video formats organized in 4 families (UGC,
  Hero/Premium, Cinematic TV-Spot, Pattern-Interrupt Viral). Each format
  uses a structure-specific prompt template. Outputs paste-ready Seedance 2.0
  prompts. NO video generation, NO API calls — just plan + prompts for the
  user's pipeline. Hebrew/English user-facing, English prompt output.
  Button-driven UX. Trigger on: "תייצר קמפיין", "תכין פרומטים לסידנס",
  "קמפיין UGC", "מפעל תוכן", "תייצר 50 פרסומות", "build a campaign",
  "Seedance campaign", "generate prompts for [product]", "ad batch", "מפעל
  פרסומות".
---

# Seedance Campaign Factory

A 3-stage pipeline: **Research → Plan → Prompts**.

**Product-agnostic.** Works for any product the user uploads. The skill
auto-detects category and adapts everything — physical rules, demographic
defaults, format selection, prompt structure.

**23 formats across 4 families.** Maximum variety per campaign. Each family
uses a different prompt structure tuned to its strengths:

| Family | Formats | Structure | When |
|---|---|---|---|
| **A — UGC** | 1–12 (Entertainment, Street Interview, Review, Unboxing, ASMR, Tutorial, GRWM, Day-in-Life, POV, Reaction, Storytime, Try-On) | 9-Layer UGC | Authenticity, person-led |
| **B — Hero/Premium** | 13–16 (Product Hero, Premium Reveal, 360, Macro) | Multi-Shot | Kinetic, no-person product |
| **C — Cinematic** | 17–20 (TV Spot, Lifestyle, Brand Story, Pro Try-On) | TV Spot Narrative | Story arc, polished |
| **D — Pattern Interrupt** | 21–23 (Visual Shock, Transformation, Wild Card) | 2-Second Hook | Viral, scroll-stopping |

Full format details: see `references/format-catalog.md`.
Full prompt templates: see `references/structures.md`.

**Output: paste-ready Seedance 2.0 prompts.** This skill does NOT call the
BytePlus API, NOT generate videos, NOT publish ads. It builds the strategic
plan and produces the final prompts. The user feeds those prompts into their
own Seedance pipeline.

**UX is button-driven.** Every clarifying question = AskUserQuestion with
2–4 concrete option buttons. Free-form typing only for product image upload
and optional name customization.

**User-facing language rule (HARD).** The user is not a developer. Do NOT
narrate technical mechanics. Send ONE clear stage banner per stage:

| Stage | Banner |
|---|---|
| 1 | **🔍 שלב 1: מחקר ורעיונות — מתחיל עכשיו.** סורק מה ויראלי השבוע בנישה של המוצר, וממיר את הטרנדים לרעיונות לסרטונים מעל 23 פורמטים. |
| 2 | **🗂️ שלב 2: תכנית תוכן — מתחיל עכשיו.** בונה את כל תכנית הסרטונים — כל סרטון ממופה לפורמט, משפחה, ופרסונה. |
| 3 | **🎬 שלב 3: כתיבת פרומטים — מתחיל עכשיו.** מייצר את הפרומטים המלאים, כל אחד במבנה המתאים למשפחה שלו. |
| 4 (אופציונלי) | **💰 שלב 4: דוח עלות — מתחיל עכשיו.** השוואה בין עלות סידנס לעומת הפקה מסורתית. |

Mirror in English if user converses in English.

---

## ONBOARDING — SINGLE-SHOT, NO PAUSES

> ⚠️ All questions in ONE AskUserQuestion call. User clicks, then pipeline runs.

**Step A — Starting stage** (button)
- "Stage 1 — Full pipeline (Recommended)"
- "Stage 2 — Build plan only (I have a brief)"
- "Stage 3 — Generate prompts only (I have a plan)"

**Step B — Video volume** (button + Other)
- "50 videos"
- "100 videos (Recommended)"
- "150 videos"
- "200 videos"
- Other → user types any number

**Step C — Default duration** (button)
- "10 seconds (Recommended — fits Reels)"
- "15 seconds (max single-clip Seedance)"
- "Mix — 8s for high-energy, 15s for ASMR / Unboxing"
- "Allow multi-chunk (some 20–30s using 2-chunk continuation)"

**Step D — Product (image and/or URL) IN THE SAME MESSAGE**

> "צרף תמונת מוצר להודעה או הדבק לינק — זה כל מה שאני צריך כדי להתחיל."

If product already attached → skip D.
If Stage 2 chosen → swap D with: "Paste your existing brief here."
If Stage 3 chosen → swap D with: "Paste or attach your content plan JSON."

**Single-message rule:** Send AskUserQuestion (A + B + C) + product-attach
prompt in the SAME message. Once user clicks and attaches, proceed straight
to the chosen stage. Don't reveal format-count split yet — that surfaces
naturally in the Stage 1 brief.

---

## SEEDANCE 2.0 GROUND TRUTH

The output is consumed by Seedance 2.0 (BytePlus ModelArk or Higgsfield).
All prompts MUST stay within these constraints.

### Hard limits (per single generation)
- **Duration:** 4–15 seconds. Longer → 2-chunk continuation.
- **Aspect ratios:** 9:16 (default for UGC/social), 16:9 (landscape), 1:1.
- **Resolution:** 480p, 720p (default), 1080p.
- **References:**
  - Up to **9 reference images** (`@Image 1` … `@Image 9`)
  - Up to **3 reference videos** (`@Video 1` … `@Video 3`, total ≤15s)
  - Up to **3 reference audios** (`@Audio 1` … `@Audio 3`, MP3, total ≤15s)
- **Audio generation:** Native — Seedance generates ambient/diegetic audio.
  Dialogue comes through reasonably. Lip-sync from non-humans: ❌ unreliable.

### Reference syntax (HARD)
- `@Image 1`, `@Image 2`, … — numbered by upload order
- `@Video 1`, … — for camera-language / continuation references
- `@Audio 1`, … — for beat-sync / mood references

Always tell the model what to take from each reference. Phrases like
"with the product from `@Image 1`", "following the camera language of
`@Video 1`", "synchronized to the beat of `@Audio 1`" are the actual work.

### Forbidden words (context-specific)

| Word | Structure A (UGC) | Structures B, C, D |
|---|---|---|
| `cinematic` | ❌ NEVER | ✅ ENCOURAGED |
| `35mm` / `film grain` | ❌ NEVER | ✅ ENCOURAGED |
| `ARRI ALEXA` / `professional color grading` | ❌ NEVER | ✅ ENCOURAGED |
| `studio` | ❌ NEVER | ❌ NEVER (use `seamless backdrop`) |
| `perfect` | ❌ NEVER | ❌ NEVER (use `clean`, `precise`) |
| `8k` / `stunning` | ❌ NEVER | ❌ NEVER |

UGC needs authenticity ("a real person filmed this on their phone"). Cinematic
language breaks that illusion. Hero/Premium/Cinematic formats benefit from
the cinematic vocabulary — Higgsfield's own official guide uses it heavily
in their multi-shot examples.

### What Seedance CANNOT do reliably
- ❌ Single clips >15s (use 2-chunk continuation)
- ❌ Reliable lip-sync from non-humans (talking objects)
- ❌ Multi-character dialogue with consistent identities across cuts
- ❌ Split-screen panels in one generation
- ❌ On-screen rendered text — comes out garbled. Add as overlays in
  post-production (CapCut, DaVinci), NOT in the Seedance prompt.

---

## PRODUCT PROFILE — auto-built per campaign

Auto-build at Stage 1 Step 1, from product image + URL.

### Auto-detect from image (silent)
1. **Category** — jewelry / beverage / skincare / haircare / makeup /
   apparel / footwear / eyewear / food / electronics / appliance / home /
   supplements / pet / software-app / service.
2. **SKUs / variants visible** (flavors, colors, sizes, scents)
3. **Packaging style + brand colors** (extract from image)
4. **Brand voice cues** — premium / Gen-Z playful / wellness / luxury /
   functional / handmade / clinical
5. **Region cues** — Hebrew → IL · Arabic / French → MENA · Cyrillic → CIS ·
   Simplified Chinese → CN · BR Portuguese → LatAm · English / no text → Global

### Auto-pick demographic defaults

| Region cue | Default audience pool |
|---|---|
| Global / English | American (Caucasian / Mexican / Asian / African / Mixed) |
| Israel (Hebrew on packaging) | Israeli (Ashkenazi / Mizrahi / Sephardi / Mixed), ages 18–35 |
| MENA | Pan-Arab / Maghrebi / Levantine |
| CIS / Eastern Europe | Slavic / Caucasian-European |
| China / SEA | East-Asian / Southeast-Asian |
| LatAm | Latin-American (varied national heritage) |
| Auto / global premium | Mixed international |

User can override via chat sentence ("make it Israeli"). Otherwise default holds.

### Diversity rule (HARD)

Across the campaign, no single persona appears more than ~15% of total
videos. Vary heritage, age band, hair, body type, style aggressively across
rows.

### Product-specific physical rules (negatives by category)

Build these into every Stage 3 prompt's negative block.

| Category | Critical physical rule | Negatives to include |
|---|---|---|
| **Rings** | ONE ring, LEFT ring finger only. Right hand bare. | "no second ring, no wedding band, no metal band on other finger, no diamond ring elsewhere, no ring on right hand" |
| **Necklaces / pendants** | ONE necklace, no layering. | "no second necklace, no layered chains, no choker plus pendant" |
| **Earrings** | Pair only, both ears matching. | "no asymmetric earrings, no third earring, no nose ring" |
| **Watches** | ONE watch, on ONE wrist. | "no two watches, no bracelet stack on the watch wrist" |
| **Eyewear** | ONE pair, brand visible on temple. | "no second pair on head, no glasses chain unless brand-specified" |
| **Single-SKU beverage** | ONE bottle in frame. Label clear in product-intro beat. | "no competitor bottle, no second bottle of same brand unless variants shot, no label-occluded grip" |
| **Multi-SKU beverage** | All variants in matching positions. | "no missing variant, no swapped order between cuts" |
| **Skincare / serum / cream** | Bottle / tube label visible. Dispenser correct orientation. | "no upside-down bottle, no label occlusion, no smudges on glass" |
| **Makeup** | Applicator handled correctly. | "no broken applicator, no melted lipstick, no smudged tip" |
| **Apparel** | Full visibility of garment in at least one beat. | "no obscuring jacket over the shirt, no pinned-up sleeves blocking the print" |
| **Footwear** | Both shoes shown together at least once. | "no single shoe alone unless product-only beat, no foot in unnatural position" |
| **Electronics / gadget** | Screen on. Power-state matches beat. | "no cracked screen, no black screen during use beat" |
| **Food / snack** | Wrapper opened cleanly. Product visible in bite/spoon beat. | "no crumbs on face, no spilled product, no upside-down wrapper" |
| **Supplements / pills** | Bottle label visible. Pills clean. | "no spilled pills, no obscured dosage panel, no medical-context" |
| **Home / kitchen tool** | Tool in actual use. Counter clean. | "no clutter behind product, no dirty surface during reveal" |
| **Pet product** | Animal in frame for product beat. | "no off-camera pet, no rough handling" |
| **App / SaaS** | Phone screen showing app UI must read. | "no rendered text errors, no wrong app on screen" |

If no row matches: fall back to "one hero product, brand label readable, no
on-screen text overlays."

### Brand mention rule

If brand is 2+ syllables OR could be mispronounced, include in talking beats
(UGC family only): *"she pronounces both syllables clearly with a small pause
between them."* Always in the CLOSING beat — never opening.

---

## STAGE 1 — Trend Research & Format Selection

> ⚠️ All research from live web searches. Auto-detect everything. Don't ask.

### Step 1 — Product detection (silent, auto)

From the product image and/or URL (use `web_fetch` if URL provided):
1. **Category** — pick from the list above.
2. **SKUs / variants visible** on packaging.
3. **Packaging / brand colors** from image.
4. **Region cue** from any text on packaging.
5. **Niche keyword** in plain English ("silicone wedding ring", "cold-pressed
   coffee", "vitamin-C serum", "running shoes").
6. **Audience default** from region table above.

### Step 2 — Compute enabled formats (silent)

Use the compatibility matrix in `references/format-catalog.md`:
- ✅ formats → enabled by default
- ⚠️ formats → enabled only if user opts in at Stage 1 Step 5
- ❌ formats → disabled by default

Cache the enabled-formats list. This drives the distribution.

### Step 3 — Run mandatory trend research (silent)

> Status line: "Pulling this week's trends…" — no query enumeration, no
> source-URL spam.

Replace `[niche]` and `[current month year]`:
1. `[niche] TikTok trending videos this week [current month year]`
2. `viral [niche] content Instagram Reels [current month year]`
3. `[niche] YouTube Shorts trending [current month year]`
4. `[niche] brand content going viral [current month year]`
5. `top [niche] ads performing [current month year]`
6. `[niche] UGC content trend [current month year]`
7. `[niche] hooks that stop the scroll [current month year]`
8. `[niche] competitor brands social media strategy [current month year]`

Then `web_fetch` the 2 most useful URLs.

### Step 4 — Synthesize the Viral Content Brief

The brief MUST include:
- **Trends table** — what's winning this week in the niche
- **Competitor patterns** — what other brands are doing
- **Hook patterns** — verbal/visual hooks the talent can use
- **Recommended Content Mix** — per-format counts, framed as a CONSEQUENCE
  of the trends, NOT as a rule. Example: "Based on what's moving this week
  in beverage content, here's the mix: 8 challenge-style UGC · 8 sidewalk
  interviews · 8 honest reviews · 8 ASMR pours · 7 product hero shots · 7
  premium reveals · …" (continues for all enabled formats).
- **20+ seed ideas** — distributed across the enabled formats.

For every seed idea, REQUIRED fields:
```
N. **[Title]**
- Format: [1 of 23 from the catalog]
- Family: [A / B / C / D]
- Duration: [4–15] seconds (or "20–30s, 2-chunk" if multi-chunk)
- Aspect ratio: 9:16 (default) | 16:9 | 1:1
- Audio: [true / false]
- Setting: [specific environment]
- Persona: [age range, gender, heritage, vibe — short — N/A if Family B]
- Scene: [≤2 sentences, what actually happens]
- Hook line: [verbal/visual hook] (N/A if no dialogue)
- Social post caption: [used in upload metadata, NEVER on-screen]
- Inspired by: [specific trend / competitor from research]
- Why viral now: [reason tied to research]
```

### Step 5 — Approval (button-driven)

```
"Brief is producible in Seedance. {N} formats enabled. What next?"
- "Looks good — proceed to Stage 2 (Recommended)"
- "Enable more formats (multi-select)"  ← shows ⚠️ list to opt in
- "Disable some formats (multi-select)" ← shows ✅ list to demote
- "Adjust mix ratios"
```

---

## STAGE 2 — Content Plan

### Goal
Two deliverables: HTML plan (human review) + structured JSON (pipeline-ready).

### Steps

**1. Confirm campaign details (single AskUserQuestion)**

Auto-derived defaults from brief + image. One AskUserQuestion covering:
- Campaign name → "Use auto: [Brand] [Niche] Campaign [current month year]" / "Different name"
- Date range → "Next 30 days (Recommended)" / "Next 60 days" / "Next 90 days" / "No dates"
- Variants → multiSelect listing every variant detected (all on by default)

Do NOT ask about format breakdown — already revealed naturally in the brief.

**2. Compute distribution**

`per_format = floor(VIDEO_COUNT / N)` where N = number of enabled formats.

Remainder distributed starting at format 1.

Examples (15 enabled formats — typical for jewelry):
- 50 videos → 3 per format + remainder 5 → 4-4-4-4-4-3-3-3-3-3-3-3-3-3-3
- 100 videos → 6 per format + remainder 10 → 7-7-7-7-7-7-7-7-7-7-6-6-6-6-6
- 150 videos → 10 per format
- 200 videos → 13 per format + remainder 5

Examples (10 enabled formats — typical for app/SaaS):
- 100 videos → 10 per format

**3. Generate the Content Plan HTML**

Save to `/mnt/user-data/outputs/[brand]-content-plan.html`. Columns:

| # | Date | Family (A/B/C/D) | Format # & name | Duration | Aspect | Audio | Setting | Persona | Scene | Hook Line | Social Caption | Goal |

Grouping:
- Group rows by **family first** (A → B → C → D), then by **format** within
  family (so all UGC rows together, then Hero, then Cinematic, then Viral).
- Within each format, vary **concept seed** from the catalog so no two
  videos in the same format are identical.
- Distribute dates evenly across the campaign window. Interleave families
  day-to-day so the feed doesn't dump 10 ASMRs back-to-back.
- Multi-chunk sequences listed as "(1/2)" + "(2/2)" with linked IDs.

Visual style: clean brand-colored header. No flashy animations.

**4. Generate the Content Plan JSON**

Save to `/mnt/user-data/outputs/[brand]-content-plan.json`:

```json
{
  "campaign_name": "...",
  "product": {
    "name": "...",
    "category": "...",
    "variants": [...],
    "brand_colors": [...],
    "region": "...",
    "audience": "..."
  },
  "total_videos": 100,
  "enabled_formats": [1, 2, 3, 4, 5, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18],
  "format_split": {
    "1_ugc_entertainment": 7,
    "2_street_interview": 7,
    "...": "..."
  },
  "videos": [
    {
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
      "setting": "kitchen",
      "persona": "...",
      "scene_summary": "...",
      "hook_line": "...",
      "social_caption_he": "...",
      "scheduled_date": "2026-05-13",
      "image_refs_required": ["product_image"],
      "video_refs_required": [],
      "prompt": null
    }
  ]
}
```

The `prompt` field stays `null` after Stage 2 — populated in Stage 3.

**5. Present**

Both files via `present_files`. Ask:
```
"Plan ready — {N} videos across {M} formats. Ready to write the Seedance prompts?"
- "Yes — write all (Recommended)"
- "Write only Family A (UGC) first for a quality check"
- "Adjust the plan first"
```

---

## STAGE 3 — Seedance 2.0 Prompt Generation

### Goal
For each video in the plan, write a complete paste-ready Seedance 2.0 prompt
using the structure matching its family.

### Routing logic

For each video row in the plan:
1. Look up `family` field (A / B / C / D).
2. Open `references/structures.md` and use the matching template.
3. Open `references/format-catalog.md` for format-specific details
   (concept seeds, persona guidance, hook patterns, audio direction).
4. Apply the Product Profile's category-specific physical rules and negatives.
5. Write the prompt following the template's layer/beat order.

### Writing routine (per video)

1. Read the row's format, family, duration, persona, setting, scene.
2. Read the matching structure template from `references/structures.md`.
3. Read the format details from `references/format-catalog.md`.
4. Read the Product Profile for category negatives.
5. Write the prompt end-to-end following the structure's template.
6. Verify:
   - Word count in target band (A: 100–260, B: 120–300, C: 180–350, D: 150–280)
   - All required elements present (consistency anchor, motion adverbs, negative block, footer)
   - Style anchor matches family rules
   - Cinematic vocab only in B/C/D — never in A
7. Populate the row's `prompt` field in the JSON.
8. Append to the human-readable Markdown grouped by family → format.

### Multi-chunk handling

For any video flagged `is_multi_chunk: true`:
- Write Chunk A's prompt with explicit ending: "Final 1-2s: silent visual beat — {character holds eye contact / hands rest on product}."
- Write Chunk B's prompt opening with: "Open on the exact visual state at the last frame of @Video 1 — {explicit description} — then continue with: {Chunk B beats}."
- Note in Chunk B's metadata: `video_refs_required: ["v[chunk_A_id]"]`.

### Output deliverables

1. **`/mnt/user-data/outputs/[brand]-prompts.json`** — the plan JSON with
   every `prompt` field populated (this is what the user's pipeline reads).
2. **`/mnt/user-data/outputs/[brand]-prompts.md`** — human-readable, grouped
   by Family → Format → Video, with one fenced ` ```prompt ` block per video:

   ````markdown
   # [Campaign] — Seedance 2.0 Prompts

   ## Family A — UGC

   ### Format 1 — UGC Entertainment (N videos)

   #### v001 — [Scene summary]
   - Duration: 10s · Aspect: 9:16 · Audio: ON
   - Image refs: product_image · Video refs: none
   - Structure: 9-Layer UGC

   ```prompt
   {full prompt here}
   ```

   ---

   #### v002 — ...
   ````

3. Present both files via `present_files`. JSON first (pipeline-ready),
   then MD (human-readable).

### Final approval

```
"Prompts written — {N} paste-ready Seedance 2.0 prompts across {M} formats. What next?"
- "Done — I'll feed these into my pipeline (Recommended)"
- "Re-write specific videos"
- "Re-write entire family (A / B / C / D)"
- "Run Stage 4 — cost comparison report"
```

---

## STAGE 4 (Optional) — Cost Comparison Report

Only on explicit user request.

### Goal
HTML report comparing **estimated Seedance/BytePlus cost** vs **estimated
traditional production cost** for the same volume.

### Steps

**1. Estimate Seedance/BytePlus cost**

Single AskUserQuestion on pricing tier:
- "Pay-as-you-go ($X per second — typical: ~$0.30/sec @ 720p, ~$0.50/sec @ 1080p)"
- "Enterprise / volume discount tier"
- "I don't know — use industry-average ($0.30/sec @ 720p)"

Compute:
- `cost_per_video = duration_seconds × rate_per_second`
- `multi_chunk_factor = 2× for any is_multi_chunk video`
- `total_cost = sum(cost_per_video × multi_chunk_factor)`

**2. Traditional cost model (baked-in 2026 industry averages)**

| Format family | Low (USD) | Mid (USD) | High (USD) |
|---|---:|---:|---:|
| UGC Entertainment / Reaction / Storytime / Day-in-Life | 250 | 750 | 1,500 |
| Street Interview | 400 | 1,200 | 2,500 |
| Unboxing | 300 | 800 | 1,500 |
| Product Review / GRWM / Tutorial / Try-On (UGC) | 300 | 900 | 2,000 |
| ASMR | 500 | 1,500 | 3,000 |
| POV First-Person | 300 | 900 | 2,000 |
| Product Hero / Hyper Motion | 3,000 | 9,000 | 15,000 |
| Premium Reveal | 2,500 | 7,500 | 12,000 |
| Product 360 / Macro | 1,500 | 4,000 | 8,000 |
| TV Spot (15s narrative) | 15,000 | 50,000 | 150,000 |
| Lifestyle Aspiration | 8,000 | 25,000 | 60,000 |
| Brand Story | 10,000 | 30,000 | 80,000 |
| Pro Virtual Try-On | 1,000 | 3,000 | 5,000 |
| Visual Shock / Transformation | 5,000 | 15,000 | 40,000 |
| Wild Card / FOOH | 30,000 | 100,000 | 500,000+ |

**Time-savings benchmark:**

| Volume | Seedance turnaround | Traditional |
|---|---|---|
| 100 mixed videos | 5–15 hours render time | 6–14 weeks production |

**3. Compute savings**

- `traditional_mid = sum(count_per_format × mid_cost)`
- `seedance_usd = total_cost` (from step 1)
- `savings_pct = 1 − seedance_usd / traditional_mid` (cap at 99.99%)

**4. Render HTML report**

Save to `/mnt/user-data/outputs/[brand]-cost-comparison.html`. Sections:
1. Hero card — "[Brand] delivered {N} videos for ~$X instead of ~$Y–$Z."
2. Volume summary table by format
3. Seedance spend breakdown
4. Traditional cost breakdown
5. Side-by-side comparison (HTML/CSS bars, no external libs)
6. Time savings panel
7. Methodology footer

**5. Present and close**

```
- "Done — close the campaign (Recommended)"
- "Adjust the rate card and re-render"
- "Run the factory again for another product"
```

---

## General Guidelines

- **Button-driven (HARD):** Every clarifying question = AskUserQuestion with
  2–4 buttons. Free-form typing only for product image / URL / custom name.
- **No-pause rule:** Bundle all clarifying questions into single calls.
- **23 formats, auto-enabled by category:** Use the compatibility matrix in
  `format-catalog.md`. User can override at Stage 1 Step 5.
- **Structure routing (HARD):** Each video's family determines its prompt
  structure. NEVER mix structures (don't use 9-Layer for a Hero shot).
- **Forbidden words are context-specific:** Cinematic vocab forbidden in
  Family A, encouraged in B/C/D. See the Forbidden Words table above.
- **No on-screen rendered text (HARD):** Every prompt's negative block
  includes the full text-suppression clause. Captions go in post-production.
- **Brand mention rule:** Brand only in closing beat (UGC family), with
  pronunciation cue for multi-syllable brands.
- **Demographic diversity (HARD):** No persona >15% of campaign. Vary
  heritage, age, hair, body type, style across rows.
- **Consistency anchor (HARD):** Every prompt that references a product
  image includes the "must remain visually unchanged" line.
- **Multi-chunk handling:** Videos >15s split into Chunk A + Chunk B with
  linked IDs and explicit visual handoff at the boundary.
- **Skip stages on request:** If user picks Stage 2 or 3 directly, honor it.
- **Hebrew/English fluidity:** Mirror the user's language in chat. Prompts
  always in English (Seedance technical requirement).
- **Failure handling:** If trend research returns thin results, surface a
  brief note ("limited fresh data this week — recommendations lean on
  evergreen patterns") and proceed.

---

## Files in this skill

- `SKILL.md` — this file (the orchestrator)
- `references/format-catalog.md` — 23 format definitions + compatibility matrix
- `references/structures.md` — 4 prompt structures (A/B/C/D) with templates and examples


## Multi-image variant sets

If the user uploads 2-9 images that are separate variants (colors/models), apply the
**Multi-Product / Variant-Set Handling** protocol at the end of
`references/structures.md` on top of every structure: role map per @Image, rotation
beats, repeated anchoring, one-variant-at-a-time, global consistency line, 2s+ per
variant time budget.
