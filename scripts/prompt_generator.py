"""
Ad prompt generator — drives claude.ai via Playwright CDP (matching the
ad-builder pattern). Uses YOUR existing Claude subscription, no API key.

Requirements:
  - Chrome running with CDP enabled (start-chrome-cdp.bat)
  - claude.ai already logged in inside that Chrome window
  - playwright installed (pip install playwright)

Public API:
  is_chrome_available() -> bool
  generate_prompts(brief, num_variations, ...) -> list[str]
"""

import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CDP_PORT = int(os.getenv("CDP_PORT", "9224"))
CDP_URL = f"http://localhost:{CDP_PORT}"
CLAUDE_NEW_URL = "https://claude.ai/new"

# ─── BACKEND SWITCH ─────────────────────────────────────────
# LLM_BACKEND env var:
#   "chrome"  = Playwright + Chrome CDP (local — uses your claude.ai login, free)
#   "api"     = Anthropic API direct (cloud — needs ANTHROPIC_API_KEY)
#   "auto"    = pick API if key set, else chrome
LLM_BACKEND = os.getenv("LLM_BACKEND", "auto").lower()


def _use_api() -> bool:
    """Decide whether to use Anthropic API or Chrome CDP."""
    if LLM_BACKEND == "api":
        return True
    if LLM_BACKEND == "chrome":
        return False
    # auto: use API if key configured AND Chrome is NOT available
    try:
        from anthropic_client import is_available as anthropic_ok
        if anthropic_ok() and not is_chrome_available():
            return True
    except Exception:
        pass
    # Prefer API in cloud (no Chrome), prefer CDP locally
    if "STREAMLIT_RUNTIME_HOSTNAME" in os.environ or "DYNO" in os.environ:
        # Running on Streamlit Cloud / Heroku / etc.
        return True
    return False



# arcads-prompts skill — embedded ruleset (UGC 9-layer formula)
SKILL_INSTRUCTIONS = """You are arcads-prompts skill — a production-grade UGC video prompt writer for Seedance 2.0. You write paste-ready prompts for ANY consumer product.

THE 9 LAYERS (in order, every prompt):
1. FORMAT HEADER — "{duration} UGC style {content_type} video, filmed on smartphone, {lighting_source}, {camera_angle}."
2. PERSON — age, gender, hair, REAL HUMAN SKIN cues (NOT plastic, NOT shiny/sweaty/blotchy). At most ONE subtle imperfection (single small mole, OR a couple barely-visible freckles only on bridge of nose, OR subtle laugh lines — pick max ONE). Specific clothing.
3. SETTING — specific space, 3+ specific clutter objects, atmosphere word, "and real"
4. PRODUCT INTRO — how they hold / use / wear / show the product, MUST include "Image 1" reference (BytePlus syntax — capitalized, with space)
5. SCRIPT BEATS — 3-4 jump cuts with timestamps [00:00], [00:04], [00:08], [00:12]; each cut has different angle/distance; dialogue lines in quotes
6. TONE DIRECTION — 3 emotion words + behavior; ALWAYS include explicit pacing cues ("pauses between thoughts", "leaves a beat of silence", "speaks at unhurried pace", "takes natural breaths between sentences")
7. EDIT STYLE — "each jump cut is slightly closer or at a different angle, as if filmed multiple takes"
8. TECHNICAL FLAWS — "lighting is {type} — {flaw}. The image is slightly imperfect — natural phone quality, not color graded, soft focus. The sound is direct from the phone mic — {ambience}"
9. VIBE STATEMENT — "The overall feel is {3 adjectives} — {relatable metaphor}"

CRITICAL RULES:
- Output ONLY fenced ```code blocks``` containing the prompts. No explanations, no headers, no commentary outside the blocks.
- Each prompt 100-260 words.
- "Image 1" appears in every prompt (capitalized, with space).
- Brand name ONLY at the very end as cleanly-separated syllables (e.g. "Thunder Fit", "Glow Drop"), with explicit pronunciation: "she/he pronounces each syllable clearly with a small pause between them"
- Casual dialogue with filler ("okay so", "literally", "I'm not even", "like"), unfinished thoughts, natural breathing
- NEVER use: acne, pimples, blemishes, rosacea, cinematic, professional, stunning, 8k, studio, perfect
- SCALE ANCHOR (mandatory in every prompt): state the product's TRUE physical size and anchor proportions to a body part ("a slim silicone ring, about 2cm, small relative to her hand" / "a palm-sized jar"). Seedance renders products oversized without an explicit scale anchor — repeat the proportion cue in at least one mid-video beat.
- NO on-screen text EVER: every negative block must include "no on-screen text, no captions, no subtitles" — Seedance renders garbled unreadable letters when captions appear.
- USE for skin: "natural human skin (not airbrushed, not plastic)", "soft matte complexion", "real skin texture you'd see on a phone screen", "rested face", "even skin tone", "minimal-makeup look". NEVER use "hint of shine", "shine on forehead", "light freckles across her face/nose", "slight unevenness", "visible pores" (Seedance amplifies these into ugly artifacts).
- Setting needs 3+ SPECIFIC objects (not generic — e.g. "stainless steel counter, wooden cutting board with chopped onions, kitchen towel over shoulder")
- All prompts in English (Seedance handles English best)

PRODUCT CONSISTENCY — core anchor for credible ads (works for ANY product type):
    * The product on screen looks IDENTICAL to Image 1 in every cut: same color, same shape, same size, same material, same finish, same label/branding. In every beat reference: "the same Image 1 product as before, unchanged".
    * If the product is WORN on the body (ring, watch, bracelet, glasses, hat, garment, headphones): anchor it to ONE specific body location and KEEP IT THERE. Pick the location once (e.g. "her LEFT ring finger" for a ring, "his right wrist" for a watch, "on her face" for glasses, "on her head" for hat). Repeat the location in every beat that shows it. NEVER let it drift, switch sides, or duplicate.
    * If the product is HANDHELD or DISPLAYED (bottle, jar, box, gadget, food, cup, phone, tool): keep it in ONE hand at a time. Anchor: "she holds the Image 1 product in her LEFT hand throughout — her right hand stays empty / out of frame / used only for action."
    * Every beat MUST specify which hand/location holds or wears the product, and what the OTHER hand is doing. Example: "[00:04] close-up of her LEFT hand pouring a drink; the Image 1 bottle is still in her LEFT hand; her right hand holds the glass."

NO OTHER PRODUCT INSTANCES, ANYWHERE — root cause of "the product changes mid-video":
    * NEVER mention any other instance of the same product type in the prompt body. NOT a "previous version", NOT an "old one", NOT a "metal one", NOT a "competitor brand", NOT "her usual one". Even in dialogue. Seedance is visual-literal — if the word "wedding ring" or "metal bottle" appears anywhere in the prompt, it WILL render that thing on screen as a SECOND object.
    * Hooks that compare to a past product MUST be REPHRASED:
        BAD:  "switched from my old metal ring"
        GOOD: "tried this and never thought about it again"
        BAD:  "my usual protein powder gave me bloating"
        GOOD: "I'd been looking for something my stomach could handle"
        BAD:  "my actual wedding ring is in a drawer"
        GOOD: "this just lives on me now"
    * The ONLY product reference allowed in the prompt body is "Image 1" / "the {generic product noun}" (referring to Image 1 only). No other product instance exists.

MULTI-PRODUCT VARIANT SETS (when several reference images are attached — e.g. 7 ring colors):
    * Each attached image is ONE separate variant: refer to them as "Image 1" ... "Image N". NEVER merge them, NEVER show a multi-pack as one object, NEVER invent unreferenced colors.
    * Rotation beats: each variant gets its own timestamped jump cut at a different angle/distance, naming its exact Image number ("[00:04] jump cut — she swaps to the ring from Image 2 on the SAME left index finger").
    * Only ONE variant visible at any moment; previous variant fully removed off-screen first. The wear/hold location is anchored once and never moves.
    * Anchor each Image number at the moment it appears AND in the consistency line: "All product references Image 1 through Image N must remain visually unchanged across cuts — same colors, materials, shapes as in their respective source images."
    * Time budget: ~2s hook + >=2s per variant + ~2s close. Too many variants for the duration -> show fewer, never rush.
    * Optional finale: all variants laid out in a row, "each matching its own source image exactly".

AUDIENCE: American consumers. ALL persons in every prompt MUST be AMERICAN — write them as Americans of various heritages, not as foreign nationals. SETTING is in the United States (American kitchens, American gyms, American suburbs/cities, American cars, American hospital scrubs, etc.).

When generating multiple variations, vary HARD between them — each variation MUST use a DIFFERENT American person along these axes:

  HERITAGE (rotate, don't repeat) — pick AMERICAN of one of these backgrounds:
    Caucasian-American (Anglo / Italian-American / Irish-American / Jewish-American / Eastern-European-American / Scandinavian-American),
    Hispanic-American / Latina-American (Mexican-American / Cuban-American / Puerto-Rican / Dominican-American / Colombian-American),
    Asian-American (Korean-American / Chinese-American / Japanese-American / Filipino-American / Vietnamese-American / Indian-American / Pakistani-American),
    African-American (Black American),
    Mixed-race American.

  AGE (rotate): mid-20s / late-20s / early-30s / mid-30s / late-30s / early-40s / mid-40s.

  HAIR (rotate): blonde, light brown, dark brown, jet black, auburn, dyed pastel,
    short pixie, shoulder-length, long, braids, afro, locs, bun, ponytail.

  BODY/STYLE (vary): athletic, soft, petite, curvy, tall — and matching American casual clothing.

  ENGLISH ACCENT: All dialogue is in casual American English. NO British, Australian, or non-American accents.

CRITICAL: Do NOT default to "young Caucasian woman with brown hair" — that is the LAZY answer. Across 3 variations, deliver 3 visually-distinct AMERICAN humans with different ages, heritages, hair, and styles. Each must read as a SPECIFIC, real, different American person.

Each prompt stands alone.

ABSOLUTE OUTPUT FORMAT (non-negotiable):
You MUST wrap each prompt in a fenced code block using triple backticks. Like this:

```
[the full 9-layer prompt for variation 1, 100-260 words]
```

```
[the full 9-layer prompt for variation 2, 100-260 words]
```

NO commentary, NO headings, NO explanations between or around the blocks. Just the fenced blocks themselves. The user pipes your output directly into a parser."""


def _candidate_urls():
    # Windows resolves "localhost" to IPv6 (::1) first, but Chrome binds to IPv4
    # only when launched with --remote-debugging-address=127.0.0.1. Try both.
    return [
        f"http://127.0.0.1:{CDP_PORT}",
        f"http://localhost:{CDP_PORT}",
    ]


def _resolve_cdp_url():
    """Find the URL variant that actually answers, or None."""
    import requests as _r
    for url in _candidate_urls():
        try:
            r = _r.get(f"{url}/json/version", timeout=2)
            if r.status_code == 200:
                return url
        except Exception:
            continue
    return None


def is_chrome_available() -> bool:
    """Check if Chrome CDP endpoint is reachable on the configured port."""
    return _resolve_cdp_url() is not None


# ──────── Playwright helpers (adapted from ad-builder/claude_browser.py) ────────

def _connect_cdp(p):
    """Connect to running Chrome via CDP, trying both IPv4 and localhost."""
    url = _resolve_cdp_url()
    if not url:
        raise RuntimeError(
            f"Cannot reach Chrome CDP on port {CDP_PORT}. "
            f"Tried: {_candidate_urls()}. "
            "Run START_CHROME.bat and keep that Chrome window open."
        )
    browser = p.chromium.connect_over_cdp(url)
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.new_page()
    return browser, context, page


def _find_input(page):
    for sel in [
        'div.ProseMirror[contenteditable="true"]',
        '[contenteditable="true"][role="textbox"]',
        '[contenteditable="true"]',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=2000):
                return loc
        except Exception:
            continue
    return None


def _paste_text(page, text):
    inp = _find_input(page)
    if not inp:
        raise RuntimeError("Could not find claude.ai input box")
    try:
        inp.click(force=True, timeout=3000)
    except Exception:
        try: inp.focus()
        except Exception: pass
    page.wait_for_timeout(200)
    page.evaluate(
        "(t) => { document.execCommand('insertText', false, t); }",
        text,
    )
    page.wait_for_timeout(300)


def _attach_images(page, image_paths):
    """Attach 1+ images to the next claude.ai message."""
    try:
        file_inputs = page.locator('input[type="file"]')
        if file_inputs.count() == 0:
            return False
        paths = [str(p) for p in image_paths]
        file_inputs.first.set_input_files(paths)
        # claude.ai needs more time to upload multiple files
        page.wait_for_timeout(2500 + 1500 * (len(paths) - 1))
        return True
    except Exception:
        return False


def _click_send(page):
    # Wait up to 30 seconds for the Send button to be visible & enabled
    for retry in range(60):
        for sel in [
            'button[aria-label="Send Message"]:not([disabled])',
            'button[aria-label*="Send" i]:not([disabled])',
            'button[type="submit"]:not([disabled])',
            'button[aria-label="Send Message"]',
        ]:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=400):
                    # Some Send buttons need a click-then-click sequence
                    btn.click(timeout=3000, force=True)
                    return True
            except Exception:
                continue
        page.wait_for_timeout(500)
    return False


def _wait_until_response_done(page, max_wait_s=600):
    deadline = time.time() + max_wait_s
    started = False
    while time.time() < deadline:
        try:
            stop_btn = page.locator('button[aria-label*="Stop"]').first
            visible = stop_btn.is_visible(timeout=400)
        except Exception:
            visible = False
        if visible:
            started = True
            time.sleep(1)
            continue
        if started:
            time.sleep(2)
            return
        time.sleep(1)
    raise TimeoutError(f"Claude response did not complete in {max_wait_s}s")


def _read_last_response(page):
    try:
        return page.evaluate(
            """() => {
                const els = document.querySelectorAll('.font-claude-response, [data-test-render-count]');
                if (!els.length) return '';
                const last = els[els.length - 1];
                return last.innerText || last.textContent || '';
            }"""
        ) or ""
    except Exception:
        return ""


def _select_opus(page, log=print):
    """Pick Claude Opus 4.7 (avoid Adaptive). If Opus 4.7 already current, skip."""
    # Step 0: check if Opus 4.7 is already the selected model
    try:
        current = page.evaluate("""() => {
            const sel = document.querySelector('button[data-testid="model-selector-dropdown"]');
            return sel ? (sel.innerText || sel.textContent || '').trim() : '';
        }""")
        if "Opus" in current and "4.7" in current and "Adaptive" not in current:
            log("    [model] already on Opus 4.7 — skip picker")
            return True
    except Exception:
        pass

    picker = None
    for sel in [
        'button[data-testid="model-selector-dropdown"]',
        'button[aria-haspopup="menu"][aria-expanded="false"]:has-text("Opus")',
        'button[aria-haspopup="menu"][aria-expanded="false"]:has-text("Sonnet")',
        'button[aria-haspopup="menu"][aria-expanded="false"]:has-text("Claude")',
        'button[aria-haspopup="menu"][aria-expanded="false"]:has-text("Adaptive")',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=800):
                picker = loc
                break
        except Exception:
            continue
    if picker is None:
        return False
    try:
        picker.click(timeout=2000)
        page.wait_for_timeout(700)
    except Exception:
        return False

    coords = page.evaluate(
        """({kw, bw}) => {
            const items = document.querySelectorAll('[role="menuitem"], [role="option"], button[data-testid*="model"]');
            const kws = kw.map(k => k.toLowerCase());
            const bws = bw.map(b => b.toLowerCase());
            for (const it of items) {
                const txt = (it.innerText || it.textContent || '').toLowerCase();
                if (kws.every(k => txt.includes(k)) && !bws.some(b => txt.includes(b))) {
                    const r = it.getBoundingClientRect();
                    return {x: r.left + r.width/2, y: r.top + r.height/2};
                }
            }
            return null;
        }""",
        {"kw": ["Opus", "4.7"], "bw": ["adaptive", "thinking", "extended"]},
    )
    if coords:
        page.mouse.click(coords["x"], coords["y"])
        page.wait_for_timeout(600)
        # Force dropdown to close — multiple Escapes + click empty area
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(150)
            page.keyboard.press("Escape")
            page.wait_for_timeout(150)
        except Exception:
            pass
        return True
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
        page.keyboard.press("Escape")
    except Exception: pass
    return False


# ──────── Public API ────────


def _parse_claude_response(response: str, num_variations: int) -> list:
    """Parse Claude's response into N prompt strings, with 3-level fallback."""
    response = response.strip()

    # Level 1: fenced ```code blocks```
    parts = response.split("```")
    if len(parts) >= 3:
        prompts = []
        for i, p_ in enumerate(parts):
            if i % 2 == 1 and p_.strip():
                first, _, rest = p_.partition("\n")
                if first and len(first) < 20 and " " not in first.strip():
                    prompts.append(rest.strip())
                else:
                    prompts.append(p_.strip())
        if prompts:
            return prompts[:num_variations]

    # Level 2: "Variation N:" / "Prompt N:" / "גרסה N:" markers
    pattern = r"(?:^|\n)\s*(?:\*\*)?(?:Variation|Variant|Prompt|Version|גרסה|Option)\s*\#?\s*(\d+)[:.\)]?\s*(?:\*\*)?\s*\n"
    matches = list(re.finditer(pattern, response, re.IGNORECASE))
    if len(matches) >= 1:
        prompts = []
        for j, m in enumerate(matches):
            start = m.end()
            end = matches[j + 1].start() if j + 1 < len(matches) else len(response)
            chunk = response[start:end].strip()
            if chunk:
                prompts.append(chunk)
        if prompts:
            return prompts[:num_variations]

    # Level 3: split on horizontal rules
    by_hr = re.split(r"\n\s*-{3,}\s*\n", response)
    if len([s for s in by_hr if s.strip()]) > 1:
        prompts = [s.strip() for s in by_hr if s.strip()]
        return prompts[:num_variations]

    # Level 4: split on repeated "{N} seconds UGC" openers (Seedance prompt header).
    # When Claude writes 2-3 prompts back-to-back without separators, each starts
    # with "15 seconds UGC..." — use that as a reliable boundary.
    header_re = re.compile(r"(?:^|\n)(\d{1,2}\s+seconds?\s+UGC[\s\S]*?)(?=(?:\n\d{1,2}\s+seconds?\s+UGC)|$)",
                           re.IGNORECASE)
    matches = [m.group(1).strip() for m in header_re.finditer(response)]
    if len(matches) > 1:
        return [m for m in matches if m][:num_variations]

    # Level 5: whole response as single prompt
    if response:
        return [response]

    raise RuntimeError("Empty response from Claude")



def call_claude_ai(user_message: str,
                    attachments: list = None,
                    log=print,
                    max_wait_s: int = 600) -> str:
    """
    Generic single-turn Claude call.
    Routes to Anthropic API (cloud) or Chrome CDP (local) based on LLM_BACKEND env.
    """
    if _use_api():
        from anthropic_client import call_claude_api
        log("  [LLM] using Anthropic API path")
        return call_claude_api(user_message, attachments=attachments, log=log)

    log("  [LLM] using Chrome CDP path")
    if not is_chrome_available():
        raise RuntimeError(
            f"Chrome with CDP not running on port {CDP_PORT}. Run START_CHROME first."
        )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("playwright not installed.")

    log(f"  [claude.ai] connecting on port {CDP_PORT}...")

    with sync_playwright() as p:
        browser, context, page = _connect_cdp(p)
        try:
            log("  [claude.ai] opening new conversation...")
            page.goto(CLAUDE_NEW_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            _select_opus(page, log=log)

            if attachments:
                from pathlib import Path as _P
                valid = [_P(a) for a in attachments if _P(a).exists()]
                if valid:
                    names = ", ".join(p_.name for p_ in valid)
                    log(f"  [claude.ai] attaching {len(valid)} file(s): {names}")
                    if not _attach_images(page, valid):
                        log("  (attach failed)")
                    page.wait_for_timeout(2500)

            # Defensive: ensure no menus/popups are open before paste
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)
            except Exception:
                pass

            log(f"  [claude.ai] pasting message ({len(user_message)} chars)...")
            _paste_text(page, user_message)
            page.wait_for_timeout(800)  # let claude.ai react to paste

            log("  [claude.ai] sending...")
            if not _click_send(page):
                page.keyboard.press("Enter")

            log("  [claude.ai] waiting for response...")
            _wait_until_response_done(page, max_wait_s=max_wait_s)

            response = _read_last_response(page)
            log(f"  [claude.ai] got response ({len(response)} chars)")
            return response
        finally:
            try: page.close()
            except Exception: pass


def generate_prompts(brief, *, num_variations=3,
                     product_description="the product",
                     brand_name="",
                     image_paths=None,
                     duration=15,
                     ratio="9:16",
                     log=print):
    """
    Generate N ad prompt variations from a free-form brief by driving claude.ai.

    Returns a list of paste-ready prompt strings.
    """
    if not is_chrome_available():
        raise RuntimeError(
            f"Chrome with CDP not running on {CDP_URL}. "
            "Run START_CHROME.bat first and make sure claude.ai is logged in."
        )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("playwright not installed. Run: pip install --user playwright")

    n_images = len(image_paths) if image_paths else 1
    image_refs = ", ".join([f"Image {i}" for i in range(1, n_images + 1)])
    image_note = (
        f"Reference {image_refs} naturally in the prompt — different cuts can feature different images."
        if n_images > 1
        else 'Reference the product as "Image 1" in the prompt.'
    )

    is_extended = duration > 15
    if is_extended:
        # User wants > 15s. We'll generate the OPENER (first 15s) here.
        # The CONTINUATION is generated separately after Video A is rendered,
        # via generate_continuation_prompt().
        constraints = f"""VIDEO TECHNICAL CONSTRAINTS (HARD — must match exactly):
  - This prompt is the OPENER (first 15 seconds) of a {duration}-second ad.
    A separate continuation prompt will be generated AFTER this video is rendered.
  - Duration of THIS prompt: EXACTLY 15 seconds.
  - Every timestamp [00:00] [00:0X] MUST fit within 15 seconds.
  - The opening line MUST say: "15 seconds UGC style ...".
  - The opener establishes: setting, person, hook, first demonstration. Leave the verdict + brand for the continuation.
  - END THE OPENER ON A COMPLETE SENTENCE — never mid-word, never mid-phrase. The last beat (around [00:13]-[00:14]) MUST contain a fully-finished spoken line + a 1-2 second SILENT visual beat (e.g. she pauses, looks at her hand, takes a breath, the camera holds on the product). This silent tail is the natural splice point.
  - Do NOT deliver the verdict, do NOT say the brand name. Save those for the continuation.
  - Aspect ratio: {ratio}.
  - Reference images attached: {n_images}. {image_note}
"""
    else:
        constraints = f"""VIDEO TECHNICAL CONSTRAINTS (HARD — must match exactly):
  - Duration: EXACTLY {duration} seconds — every timestamp [00:00] [00:0X] MUST fit within {duration} seconds.
  - The opening line MUST say: "{duration} seconds UGC style ...".
  - Aspect ratio: {ratio}.
  - Reference images attached: {n_images}. {image_note}
"""

    user_msg = f"""{SKILL_INSTRUCTIONS}

---

Brief: {brief}

Product description: {product_description}
Brand name (mention only at end of the FULL ad, as two separated words): {brand_name}
Number of variations: {num_variations}

{constraints}

Generate {num_variations} UGC video prompt(s) following the 9-layer formula. Each prompt 100-260 words, in its own fenced ```code block```. Vary the hook, setting, tone, and persona between variations. Output ONLY the fenced code blocks — no commentary."""

    log(f"  [claude.ai] connecting to Chrome on port {CDP_PORT}...")

    with sync_playwright() as p:
        browser, context, page = _connect_cdp(p)
        try:
            log("  [claude.ai] opening new conversation...")
            page.goto(CLAUDE_NEW_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)

            _select_opus(page, log=log)

            if image_paths:
                valid_paths = [Path(p) for p in image_paths if Path(p).exists()]
                if valid_paths:
                    names = ", ".join(p.name for p in valid_paths)
                    log(f"  [claude.ai] attaching {len(valid_paths)} image(s): {names}")
                    if not _attach_images(page, valid_paths):
                        log("  (image attach failed — continuing without images)")

            log("  [claude.ai] pasting prompt...")
            _paste_text(page, user_msg)
            page.wait_for_timeout(500)

            log("  [claude.ai] sending...")
            if not _click_send(page):
                page.keyboard.press("Enter")

            log("  [claude.ai] waiting for response (up to 10 min)...")
            _wait_until_response_done(page, max_wait_s=600)

            response = _read_last_response(page)
            log(f"  [claude.ai] got response ({len(response)} chars)")
        finally:
            try: page.close()
            except Exception: pass

    return _parse_claude_response(response, num_variations)


def generate_continuation_prompt(
    *,
    opener_prompt: str,
    brief: str,
    image_paths: list = None,
    video_path = None,
    last_frame_path = None,
    target_duration: int = 15,
    brand_name: str = "",
    log=print,
):
    """
    Generate the CONTINUATION prompt (next chunk after Video A).

    Sends Claude:
      - The original opener prompt (so it knows what already happened)
      - The original product image(s) (so the product stays consistent)
      - The previous video clip (so it sees the visual state)
      - The last frame of the previous video (extra visual cue)
      - The original brief
      - Target duration for THIS chunk

    Returns one continuation prompt string.
    """
    use_api = _use_api()
    if not use_api and not is_chrome_available():
        try:
            from anthropic_client import is_available as _anth_ok
            if _anth_ok():
                use_api = True
            else:
                raise RuntimeError(
                    f"Chrome CDP not running on port {CDP_PORT} AND ANTHROPIC_API_KEY missing."
                )
        except Exception as _e:
            raise RuntimeError(
                f"Chrome CDP not running on port {CDP_PORT} and Anthropic API unavailable: {_e}"
            )
    if not use_api:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("playwright not installed.")

    n_user_images = len(image_paths) if image_paths else 0
    extra_attachments = []
    if video_path and Path(video_path).exists():
        extra_attachments.append(Path(video_path))
    if last_frame_path and Path(last_frame_path).exists():
        extra_attachments.append(Path(last_frame_path))
    all_attachments = (image_paths or []) + extra_attachments

    user_msg = f"""{SKILL_INSTRUCTIONS}

---

CONTINUATION TASK — write the NEXT segment of an existing ad.

ORIGINAL BRIEF: {brief}

OPENER PROMPT (what was just rendered as Video 1, attached above):
```
{opener_prompt}
```

ATTACHMENTS (in order):
  - First {n_user_images} image(s) = the original product reference image(s) ("Image 1"...{f'"Image {n_user_images}"' if n_user_images > 1 else ''}).
  - Then the MP4 of the just-rendered opener video.
  - Then a JPG of the LAST FRAME of that opener video (this is the EXACT visual state where the new segment must begin).

YOUR TASK:
Write ONE 9-layer UGC video prompt that picks up EXACTLY from the last frame of the opener and continues to deliver the rest of the ad. Constraints:

  - Duration: EXACTLY {target_duration} seconds.
  - Opening line MUST say: "{target_duration} seconds UGC style ...".
  - The PERSON, OUTFIT, SETTING, LIGHTING must be IDENTICAL to the opener (Video 1 shows them clearly).
  - The first beat [00:00] of THIS continuation MUST flow directly from the last frame of Video 1 — the same hand position, the same gaze, the same breath. The continuation begins with a SHORT silent beat (0.5-1s) before any new dialogue, so the splice with Video 1 looks like a natural take cut, NOT a hard scene change.
  - PRODUCT CONSISTENCY — same rule as opener. The product stays anchored to ONE location (the same body part / hand from Video 1). Every beat must specify which hand or body location holds/wears it; the other hand stays empty or used only for action. The product NEVER duplicates, switches sides, or changes appearance.
  - PRODUCT CONTINUITY: shape/color/material/finish/labeling identical to Image 1 in every cut. Reference "the same Image 1 product, unchanged" in each beat that shows it.
  - Reference Image 1 = the EXACT visual state to start from (last frame of Video 1).
  - The opener establishes setup + first demo. THIS continuation must deliver: the proof/result + the verdict + the brand name "{brand_name}" at the end with explicit pronunciation cue ("she pronounces both syllables clearly with a small pause between them").
  - First [00:00] beat must match the action of the last frame visually.
  - Output ONE fenced ```code block``` — no commentary.

Output the continuation prompt now."""

    # ── API path (cloud) ──
    if use_api:
        log("  [anthropic API] generating continuation prompt...")
        from anthropic_client import call_claude_api
        api_attachments = [Path(p_) for p_ in (image_paths or []) if Path(p_).exists()]
        if last_frame_path and Path(last_frame_path).exists():
            api_attachments.append(Path(last_frame_path))
        api_msg = user_msg.replace(
            "  - Then the MP4 of the just-rendered opener video.\n",
            "",
        )
        response = call_claude_api(api_msg, attachments=api_attachments, log=log)
        parts = response.split("```")
        for i, p_ in enumerate(parts):
            if i % 2 == 1 and p_.strip():
                first, _, rest = p_.partition("\n")
                if first and len(first) < 20 and " " not in first.strip():
                    return rest.strip()
                return p_.strip()
        if response.strip():
            return response.strip()
        raise RuntimeError("Empty continuation response from Anthropic API")

    # ── CDP path (local) ──
    log(f"  [claude.ai] connecting on port {CDP_PORT} for continuation...")

    with sync_playwright() as p:
        browser, context, page = _connect_cdp(p)
        try:
            log("  [claude.ai] opening new conversation (continuation)...")
            page.goto(CLAUDE_NEW_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            _select_opus(page, log=log)

            valid = [Path(a) for a in all_attachments if Path(a).exists()]
            if valid:
                names = ", ".join(p_.name for p_ in valid)
                log(f"  [claude.ai] attaching {len(valid)} file(s): {names}")
                if not _attach_images(page, valid):
                    log("  (attach failed)")
                # videos take longer to upload
                page.wait_for_timeout(2500)

            log("  [claude.ai] pasting continuation prompt...")
            _paste_text(page, user_msg)
            page.wait_for_timeout(500)

            log("  [claude.ai] sending...")
            if not _click_send(page):
                page.keyboard.press("Enter")

            log("  [claude.ai] waiting for continuation...")
            _wait_until_response_done(page, max_wait_s=600)

            response = _read_last_response(page)
            log(f"  [claude.ai] got continuation ({len(response)} chars)")
        finally:
            try: page.close()
            except Exception: pass

    parts = response.split("```")
    for i, p_ in enumerate(parts):
        if i % 2 == 1 and p_.strip():
            first, _, rest = p_.partition("\n")
            if first and len(first) < 20 and " " not in first.strip():
                return rest.strip()
            return p_.strip()
    if response.strip():
        return response.strip()
    raise RuntimeError("Empty continuation response from Claude")


# Backward compatibility alias
def is_available():
    return is_chrome_available()


if __name__ == "__main__":
    print(f"Chrome CDP available: {is_chrome_available()}")
    if is_chrome_available():
        prompts = generate_prompts(
            "Ad for any consumer product — a basketball coach in his 30s recommending something. Hook: comfort during practice.",
            num_variations=1,
        )
        print(f"\nGot {len(prompts)} prompts.")
        for i, p in enumerate(prompts, 1):
            print(f"\n--- Prompt {i} ({len(p)} chars) ---\n{p[:400]}...")
