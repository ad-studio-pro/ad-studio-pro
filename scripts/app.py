"""
Ad Studio Pro — 3-stage campaign factory UI.
Stage 1: detect product + trend research → viral brief
Stage 2: generate plan JSON for N videos
Stage 3: generate per-video prompts
(Stage 4: render videos via BytePlus — optional)
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import importlib

# ── Streamlit Cloud → push every secret into os.environ BEFORE we import
# any of our own modules, so their `os.getenv(...)` calls find the values
# (otherwise they snapshot an empty value at import time).
try:
    for _k, _v in dict(st.secrets).items():
        if isinstance(_v, (str, int, float)):
            os.environ.setdefault(str(_k), str(_v))
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

# ── AUTH GATE (Google OAuth, @neobrands.io only) ─────────────
# Must run BEFORE st.set_page_config in the body of the app so the
# landing/rejection screens can set their own page configs.
from auth_gate import require_login, render_logout_button
_user = require_login()  # blocks via st.stop() if not authorized

# Core modules
from byteplus_client import submit_task, poll_task, download_video, extract_video_url
from upload_image import upload_image, IMGBB_API_KEY
from upload_video import upload_video
from video_stitcher import extract_last_frame, concat_videos, is_ffmpeg_available

# Pipeline modules
import prompt_generator as pg
import stage1_runner
import stage2_runner
import stage3_runner
from stage1_research import GEMINI_API_KEY, TAVILY_API_KEY
from stage2_plan import ALL_FORMATS, compute_format_split

# Hot-reload pipeline modules on every script run
for mod in (pg, stage1_runner, stage2_runner, stage3_runner):
    importlib.reload(mod)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

st.set_page_config(page_title="Ad Studio Pro", page_icon="🎬", layout="wide",
                   initial_sidebar_state="collapsed")

# Branded theme (CSS + RTL) and hero header.
# Reload first — Streamlit Cloud hot-reloads app.py on git push but keeps
# imported modules cached in the running process; without this, new functions
# in ui_theme raise ImportError until a manual reboot.
import anthropic_client as _anthropic_mod
importlib.reload(_anthropic_mod)
import ui_theme as _ui_theme_mod
importlib.reload(_ui_theme_mod)
from ui_theme import inject_theme, render_hero, render_stepper, compute_full_pipeline_steps
inject_theme()
render_hero(_user.get("email", ""))
# st.title("🎬 Ad Studio Pro")  # replaced by render_hero


# ════════════════════════════════════════════════════════════
# Sidebar — collapsible status (closed by default)
# ════════════════════════════════════════════════════════════
chrome_ok = pg.is_chrome_available()

# Detect cloud: Streamlit Cloud sets HOME=/home/adminuser and works from /mount/src/
_IS_CLOUD = (
    str(PROJECT_ROOT).startswith("/mount/")
    or os.environ.get("HOME", "").startswith("/home/adminuser")
)

with st.sidebar:
    st.header("⚙️ Status")
    # Claude.ai (Chrome CDP) row removed — irrelevant in cloud, distracting locally.

    # Anthropic API (cloud fallback)
    try:
        from anthropic_client import is_available as _anth_ok
        anthropic_ok = _anth_ok()
    except Exception:
        anthropic_ok = False
    title = f"{'✅' if anthropic_ok else '⚠️'} Anthropic API (cloud)"
    with st.expander(title, expanded=False):
        if anthropic_ok:
            st.write("Anthropic API is configured. Claude will run via the API (cloud mode).")
        else:
            st.warning("ANTHROPIC_API_KEY is missing in Streamlit Secrets")
            st.write("Get one at https://console.anthropic.com/")

    # Gemini
    title = f"{'✅' if GEMINI_API_KEY else '⚠️'} Gemini Vision + Nano Banana 2"
    with st.expander(title, expanded=False):
        if GEMINI_API_KEY:
            st.write("Used for 2 things:")
            st.write("1. **Stage 1**: automatic product-category detection from an image")
            st.write("2. **Nano Banana 2**: scene image generation (optional)")
        else:
            st.warning("GEMINI_API_KEY is missing in .env")
            st.write("Get one for free at https://aistudio.google.com/apikey")

    # Tavily
    title = f"{'✅' if TAVILY_API_KEY else '⚠️'} Tavily web search"
    with st.expander(title, expanded=False):
        if TAVILY_API_KEY:
            st.write("Runs 8 web searches to gather trends in the product's niche.")
        else:
            st.warning("TAVILY_API_KEY is missing in .env")
            st.write("Get one at https://tavily.com/")

    # imgbb
    title = f"{'✅' if IMGBB_API_KEY else '⚠️'} imgbb image hosting"
    with st.expander(title, expanded=False):
        if IMGBB_API_KEY:
            st.write("Uploads product images to a public host so BytePlus can fetch them.")
        else:
            st.warning("IMGBB_API_KEY is missing in .env")

    # ffmpeg
    title = f"{'✅' if is_ffmpeg_available() else '⚠️'} ffmpeg ready"
    with st.expander(title, expanded=False):
        if is_ffmpeg_available():
            st.write("ffmpeg is available via imageio-ffmpeg.")
            st.write("Used for: extracting the last frame + stitching chunks into a long video.")
        else:
            st.warning("ffmpeg is missing. Run 1_SETUP.bat again.")

    st.markdown("---")
    st.subheader("Pipeline state")
    st.write(f"- Stage 1: {'✅' if st.session_state.get('stage1') else '⬜'}")
    st.write(f"- Stage 2: {'✅' if st.session_state.get('stage2') else '⬜'}")
    st.write(f"- Stage 3: {'✅' if st.session_state.get('stage3') else '⬜'}")

    st.markdown("---")
    if st.button("🔄 Refresh status", use_container_width=True):
        st.rerun()
    if st.button("🗑 Reset pipeline", use_container_width=True):
        for k in ("stage1", "stage2", "stage3", "image_path", "brief_text"):
            st.session_state.pop(k, None)
        st.rerun()

# Show logged-in user + logout in the sidebar.
render_logout_button()

# Voice mode (Seed Audio 1.0). If active, it takes over the whole page.
import audio_studio as _audio_studio_mod
importlib.reload(_audio_studio_mod)
from audio_studio import maybe_render_audio_studio
if maybe_render_audio_studio(PROJECT_ROOT):
    st.stop()

# Express mode (paste prompts → videos). Renders mode selector + Express UI.
import express_mode as _express_mode_mod
importlib.reload(_express_mode_mod)
from express_mode import maybe_render_express
IS_EXPRESS = maybe_render_express(PROJECT_ROOT)

# === EXPRESS-MODE WRAP — hides Stage 0-3 when Express is active ===
if not IS_EXPRESS:

    # ════════════════════════════════════════════════════════════
    # Stage 0 — Inputs
    # ════════════════════════════════════════════════════════════
    render_stepper(compute_full_pipeline_steps(st.session_state))
    st.header("1️⃣ Upload product images + pick parameters")
    st.caption("Upload 1-9 images (product, colors, components, angles) — each image becomes an @Image you can show in the video.")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        uploaded_files = st.file_uploader(
            "Product images (up to 9 — first = Image 1, second = Image 2, etc.)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        if uploaded_files:
            save_dir = PROJECT_ROOT / "assets" / "product"
            save_dir.mkdir(parents=True, exist_ok=True)
            image_paths = []
            for uf in uploaded_files[:9]:  # BytePlus max 9
                path = save_dir / uf.name
                path.write_bytes(uf.getvalue())
                image_paths.append(str(path))
            st.session_state["image_paths"] = image_paths
            # Backward-compat — first image is the "primary" for Gemini Vision
            st.session_state["image_path"] = image_paths[0]

            # Thumbnails row + per-image role tags
            thumb_cols = st.columns(min(len(image_paths), 5))
            for idx, ip in enumerate(image_paths):
                with thumb_cols[idx % 5]:
                    st.image(ip, width=120, caption=f"Image {idx+1}")

            if len(image_paths) > 1:
                st.caption(
                    "🏷 **Role for each image (recommended!)** — Claude will use this to combine "
                    "all the products/components correctly in one video (@Image 1, @Image 2...)."
                )
                image_roles = []
                role_cols = st.columns(min(len(image_paths), 3))
                for idx, ip in enumerate(image_paths):
                    with role_cols[idx % 3]:
                        role = st.text_input(
                            f"@Image {idx+1}",
                            key=f"img_role_{idx}",
                            placeholder="e.g.: bottle - front / measuring scoop / packaging from behind",
                        )
                        image_roles.append(role.strip())
                st.session_state["image_roles"] = image_roles
            else:
                st.session_state["image_roles"] = []

    with col_b:
        sub_a, sub_b = st.columns(2)
        with sub_a:
            total_videos = st.selectbox(
                "How many videos to create?",
                [1, 3, 5, 10, 20, 50, 100, 200],
                index=2,
                help="Automatic distribution: 1=Product Review, 5=a mix of formats, 100+=all 23 formats",
            )
            default_duration = st.selectbox(
                "Default duration (seconds)",
                [5, 8, 10, 15, 20, 25, 30],
                index=3,
                format_func=lambda x: f"{x}s" + (" (×2 chunks)" if x > 15 else ""),
                help="≤15s = a single generation. 20-30s = two chunks (opener+continuation) stitched automatically with ffmpeg.",
            )
            duration_policy = st.radio(
                "Duration policy",
                ["Strict — always use my duration", "Flexible — Claude may suggest otherwise based on the format/research"],
                index=1,
                help="Strict: all videos use the duration you picked. Flexible: if the research recommends 25s for a Storytime, Claude writes 25s and we generate 2 chunks."
            )
            max_duration = st.selectbox(
                "Maximum allowed (Flexible mode)",
                [15, 20, 25, 30],
                index=3,
                help="In Flexible mode — Claude can go up to this cap. Over 15s = multi-chunk."
            )
            audience = st.selectbox(
                "Target audience",
                ["American", "Israeli", "Pan-Arab / MENA", "Slavic / CIS",
                 "East Asian", "Latin American", "Mixed international"],
                index=0,
                help="Overrides Gemini's automatic detection. Affects: character heritage, setting (American kitchen/gym/etc.), accent.",
            )
        with sub_b:
            campaign_name = st.text_input("Campaign name (optional)", placeholder="auto-generated")
            date_range = st.selectbox("Date range", ["30 days", "60 days", "90 days", "no dates"])
            brand_input = st.text_input("Brand name (optional, overrides detection)", placeholder="auto-detected from packaging")

    # Notes — free-form context that affects all 3 stages
    st.markdown("**💬 Free-form notes (optional) — passed to every stage**")
    user_notes = st.text_area(
        "Any extra info that helps Claude fine-tune the campaign",
        height=120,
        placeholder=(
            "For example:\n"
            "- Exact target audience: women 40-60 with back/leg pain\n"
            "- The product is recommended by orthopedists, not just for general pain\n"
            "- We sell mainly on Amazon US, less DTC\n"
            "- Avoid medical claims (FDA compliance)\n"
            "- Strongest selling point: noticeable relief within 3 days\n"
            "- Never mention competitors\n"
        ),
        help="This text is sent to Claude at every stage — Stage 1 (brief), Stage 2 (plan), Stage 3 (prompts). More detail → more accuracy.",
        label_visibility="collapsed",
    )


    # ════════════════════════════════════════════════════════════
    # STAGE 1 — Research
    # ════════════════════════════════════════════════════════════
    st.header("2️⃣ Stage 1: Trend research + product analysis")

    # LLM is available if Chrome+CDP is up locally OR the Anthropic API key is set (cloud).
    try:
        from anthropic_client import is_available as _anthropic_ok
        llm_ok = chrome_ok or _anthropic_ok()
    except Exception:
        llm_ok = chrome_ok
    s1_disabled = not st.session_state.get("image_path") or not llm_ok or not GEMINI_API_KEY or not TAVILY_API_KEY
    if st.button("🔍 Run Stage 1 — Research", type="primary", disabled=s1_disabled,
                  help="Requires: an image + (Chrome or Anthropic API) + Gemini + Tavily" if s1_disabled else None):
        with st.status("🔍 Stage 1 running...", expanded=True) as s:
            try:
                result = stage1_runner.run_stage1(
                    image_path=Path(st.session_state["image_path"]),
                    total_videos=total_videos,
                    duration=default_duration,
                    audience_override=audience,
                    user_notes=user_notes.strip(),
                    log=lambda m: s.write(m),
                )
                # User-typed brand overrides what Gemini detected
                if brand_input.strip():
                    result["product"]["brand_name_visible"] = brand_input.strip()
                st.session_state["stage1"] = result
                # Auto-trigger Smart Pick now that we have research data
                s.write("🤖 Claude is picking optimal formats from the research (automatically)...")
                try:
                    smart_split = stage1_runner.recommend_formats_from_research(
                        stage1_result=result,
                        total_videos=total_videos,
                        enabled_format_pool=list(ALL_FORMATS.keys()),
                        user_notes=user_notes.strip(),
                        log=lambda m: s.write(m),
                    )
                    st.session_state["smart_pick"] = smart_split
                    s.write(f"✓ Smart Pick: {len(smart_split)} formats chosen based on the research")
                except Exception as sp_e:
                    s.write(f"⚠ Smart Pick failed ({sp_e}) — try manually after Stage 1")
                s.update(label="✅ Stage 1 + Smart Pick completed", state="complete", expanded=False)
            except Exception as e:
                s.update(label=f"❌ {e}", state="error", expanded=True)

    if st.session_state.get("stage1"):
        s1 = st.session_state["stage1"]
        with st.expander("📦 Product Profile (auto-detected)", expanded=False):
            # Editable product JSON
            prod_text = st.text_area(
                "Edit product details (JSON)",
                value=json.dumps(s1["product"], indent=2, ensure_ascii=False),
                height=260,
                key="product_edit",
            )
            if st.button("💾 Save product details", key="save_product"):
                try:
                    s1["product"] = json.loads(prod_text)
                    st.session_state["stage1"] = s1
                    st.success("✓ Saved")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")

        with st.expander("📄 Viral Content Brief — manually editable", expanded=True):
            brief_edited = st.text_area(
                "Edit the Brief — anything you change here affects Stage 2",
                value=s1["viral_brief"],
                height=400,
                key="brief_edit",
                label_visibility="collapsed",
            )
            if st.button("💾 Save Brief", key="save_brief"):
                s1["viral_brief"] = brief_edited
                st.session_state["stage1"] = s1
                st.success("✓ Brief saved. Stage 2 will use the new version.")

    # Skip-stage-1 expander: paste your own brief
    with st.expander("✏️ Option: skip Stage 1 — write your own Brief", expanded=False):
        st.caption("If you already have a Brief and don't need research — paste it here and continue to Stage 2.")
        manual_brief = st.text_area(
            "Manual Brief",
            height=300,
            placeholder="Paragraph 1: why this problem is burning for the audience...\nParagraph 2: the viral angles...\nParagraph 3: creative foundations...",
            key="manual_brief_input",
            label_visibility="collapsed",
        )
        manual_product_json = st.text_area(
            "Manual product details (JSON) — optional; if left empty Claude won't know what the product is",
            value='{\n  "category": "",\n  "subtype": "",\n  "skus_visible": [],\n  "brand_name_visible": "",\n  "packaging_colors": [],\n  "packaging_style": "",\n  "region_cue": "global",\n  "niche_keyword": "",\n  "audience_default": "American"\n}',
            height=240,
            key="manual_product_input",
        )
        if st.button("✅ Use the manual input (skip Stage 1)", key="use_manual_brief"):
            if not manual_brief.strip():
                st.error("You need to write a Brief")
            else:
                try:
                    manual_product = json.loads(manual_product_json) if manual_product_json.strip() else {}
                    st.session_state["stage1"] = {
                        "product": manual_product,
                        "viral_brief": manual_brief.strip(),
                        "research": {"manual": True},
                    }
                    st.success("✓ Manual Stage 1 saved. You can continue to Stage 2.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Product details JSON is invalid: {e}")


    # ════════════════════════════════════════════════════════════
    # Format selection — AFTER Stage 1, auto-picked by research
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    with st.expander(f"🎯 Format selection ({total_videos} videos) — view / override the automatic pick", expanded=False):
        # Compute the auto-picked formats
        auto_split = compute_format_split(total_videos, list(ALL_FORMATS.keys()))
        auto_picked = sorted([f for f, c in auto_split.items() if c > 0], key=lambda f: -auto_split.get(f, 0))

        # SMART PICK button — uses research from Stage 1 to let Claude decide
        smart_disabled = not st.session_state.get("stage1") or not llm_ok
        smart_help = (
            "You must run Stage 1 first (so Claude has research to work with) + an active Chrome"
            if smart_disabled else
            "Claude will pick formats based on the research and the specific product — not a generic priority"
        )
        if st.button("🤖 Smart Pick — let Claude choose based on the research",
                      disabled=smart_disabled, help=smart_help, use_container_width=True):
            with st.spinner("Claude is picking optimal formats from the research..."):
                try:
                    smart_split = stage1_runner.recommend_formats_from_research(
                        stage1_result=st.session_state["stage1"],
                        total_videos=total_videos,
                        enabled_format_pool=list(ALL_FORMATS.keys()),
                        user_notes=user_notes.strip(),
                        log=lambda m: st.write(m),
                    )
                    st.session_state["smart_pick"] = smart_split
                    st.success(f"✅ Smart pick: {sum(smart_split.values())} videos, {len(smart_split)} formats")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Smart Pick failed: {e}")

        # Decide which split to display as default in the multiselect
        if st.session_state.get("smart_pick"):
            smart = st.session_state["smart_pick"]
            default_pool = sorted(smart.keys(), key=lambda f: -smart.get(f, 0))
            st.markdown(f"**Smart Pick from Claude (research-based):** {len(default_pool)} formats")
            for fn, cnt in smart.items():
                st.caption(f"  - Format #{fn} {ALL_FORMATS[fn][2]}: ×{cnt}")
            st.markdown("")
            st.markdown(f"**You can edit** ({len(auto_picked)} in the generic priority, or Smart Pick above):")
            default_selection = default_pool
        else:
            st.markdown(f"**Automatic default** ({len(auto_picked)} formats chosen by priority):")
            default_selection = auto_picked.copy()
    

        # Format label helper
        def fmt_label(f_num):
            name, fam, display = ALL_FORMATS[f_num]
            count = auto_split.get(f_num, 0)
            return f"[Family {fam}] #{f_num} {display}" + (f"  ×{count}" if count > 0 else "")

        # Show all 23 with the chosen pre-selection
        all_format_options = list(ALL_FORMATS.keys())

        selected_formats = st.multiselect(
            "Formats to include in the campaign",
            options=all_format_options,
            default=default_selection,
            format_func=fmt_label,
            help="Default = the automatic pick. Add/remove as you like. If you pick fewer formats than videos, some formats get more than one."
        )

        if selected_formats:
            manual_split = compute_format_split(total_videos, selected_formats)
            active_split = {k: v for k, v in manual_split.items() if v > 0}
            st.info(f"💡 You will get **{sum(active_split.values())} videos in {len(active_split)} formats**: " +
                    ", ".join(f"{ALL_FORMATS[f][2]} ×{c}" for f, c in active_split.items()))
            # Save the selection so Stage 2 uses it
            st.session_state["selected_formats"] = selected_formats
        else:
            st.warning("⚠️ No formats selected — Stage 1 will rely on the automatic default")
            st.session_state["selected_formats"] = None


    # ════════════════════════════════════════════════════════════
    # STAGE 2 — Plan
    # ════════════════════════════════════════════════════════════
    st.header("3️⃣ Stage 2: Campaign plan")

    s2_disabled = not st.session_state.get("stage1") or not llm_ok
    if st.button("🗂 Run Stage 2 — Plan", type="primary", disabled=s2_disabled):
        with st.status("🗂 Stage 2 running...", expanded=True) as s:
            try:
                s1 = st.session_state["stage1"]
                days = int(date_range.split()[0]) if "day" in date_range else 30
                date_start = datetime.now().strftime("%Y-%m-%d")
                date_end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

                # Use user's manual format selection if they made one, else auto
                user_selection = st.session_state.get("selected_formats")
                if user_selection:
                    split = compute_format_split(total_videos, user_selection)
                    enabled = [f for f, c in split.items() if c > 0]
                else:
                    split = compute_format_split(total_videos, list(ALL_FORMATS.keys()))
                    enabled = [f for f, c in split.items() if c > 0]

                n_imgs = len(st.session_state.get("image_paths", [st.session_state.get("image_path")]))
                plan = stage2_runner.run_stage2(
                    product=s1["product"],
                    viral_brief=s1["viral_brief"],
                    total_videos=total_videos,
                    enabled_formats=enabled,
                    campaign_name=campaign_name,
                    date_start=date_start,
                    date_end=date_end,
                    default_duration=default_duration,
                    duration_policy="flexible" if "Flexible" in duration_policy else "strict",
                    max_duration=max_duration,
                    user_notes=user_notes.strip(),
                    n_images=n_imgs,
                    log=lambda m: s.write(m),
                )
                st.session_state["stage2"] = plan
                s.update(label=f"✅ Stage 2 completed — {len(plan.get('videos', []))} rows in the plan",
                         state="complete", expanded=False)
            except Exception as e:
                s.update(label=f"❌ {e}", state="error", expanded=True)

    if st.session_state.get("stage2"):
        plan = st.session_state["stage2"]
        st.subheader(f"📋 {plan.get('campaign_name', 'Campaign')}")
        st.caption(f"{plan.get('total_videos')} videos · {len(plan.get('enabled_formats', []))} formats")

        if "_files" in plan:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"📄 [Plan JSON]({plan['_files'].get('json', '')})")
            with c2:
                st.markdown(f"🌐 [Plan HTML]({plan['_files'].get('html', '')})")

        with st.expander("📋 Plan rows (preview)", expanded=True):
            videos = plan.get("videos", [])
            if videos:
                preview = [{
                    "id": v.get("id"),
                    "family": v.get("family"),
                    "format": v.get("format_name"),
                    "dur": f"{v.get('duration_seconds')}s",
                    "setting": v.get("setting", "")[:30],
                    "persona": v.get("persona", "")[:40],
                    "hook": v.get("hook_line", "")[:50],
                } for v in videos]
                st.dataframe(preview, use_container_width=True)

        # Editable plan JSON
        with st.expander("✏️ Edit the plan manually (JSON) — changes affect Stage 3", expanded=False):
            plan_text = st.text_area(
                "Plan JSON",
                value=json.dumps(plan, indent=2, ensure_ascii=False),
                height=500,
                key="plan_edit",
                label_visibility="collapsed",
            )
            if st.button("💾 Save plan", key="save_plan"):
                try:
                    new_plan = json.loads(plan_text)
                    st.session_state["stage2"] = new_plan
                    st.success(f"✓ Plan saved — {len(new_plan.get('videos', []))} videos")
                    st.rerun()
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")

    # Skip-stage-2 expander
    with st.expander("✏️ Option: skip Stage 2 — write your own plan", expanded=False):
        st.caption("If you already have a plan (JSON with a videos field) — paste it here.")
        manual_plan = st.text_area(
            "Manual plan",
            height=320,
            placeholder='{\n  "campaign_name": "...",\n  "videos": [\n    {"id": 1, "format": 1, "family": "UGC", "format_name": "...", "duration_seconds": 15, "setting": "...", "persona": "...", "hook_line": "..."}\n  ]\n}',
            key="manual_plan_input",
            label_visibility="collapsed",
        )
        if st.button("✅ Use the manual plan (skip Stage 2)", key="use_manual_plan"):
            if not manual_plan.strip():
                st.error("You need to write a plan")
            else:
                try:
                    new_plan = json.loads(manual_plan)
                    if "videos" not in new_plan:
                        st.error("A 'videos' field is required")
                    else:
                        st.session_state["stage2"] = new_plan
                        st.success(f"✓ Manual plan saved — {len(new_plan.get('videos', []))} videos")
                        st.rerun()
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")


    # ════════════════════════════════════════════════════════════
    # STAGE 3 — Prompts
    # ════════════════════════════════════════════════════════════
    st.header("4️⃣ Stage 3: Writing prompts for each video")

    s3_disabled = not st.session_state.get("stage2") or not llm_ok
    col_s3a, col_s3b = st.columns([1, 3])
    with col_s3a:
        s3_limit = st.number_input("Limit to the first N videos (0=all)",
                                    min_value=0, max_value=200, value=0, step=1,
                                    help="For testing: try just 2-3 before generating everything")
    with col_s3b:
        if st.button("✍️ Run Stage 3 — Prompts", type="primary", disabled=s3_disabled, use_container_width=True):
            with st.status("✍️ Stage 3 running (time: ~30s per video)...", expanded=True) as s:
                try:
                    plan = dict(st.session_state["stage2"])  # mutable copy
                    product = st.session_state["stage1"]["product"]
                    image_path = Path(st.session_state["image_path"])

                    progress_bar = s.progress(0.0)
                    def progress_cb(i, total):
                        progress_bar.progress(i / total, text=f"Video {i}/{total}")

                    plan_done = stage3_runner.run_stage3(
                        plan=plan,
                        product=product,
                        image_path=image_path,
                        image_paths=[Path(ip) for ip in st.session_state.get("image_paths", [str(image_path)])],
                        image_roles=st.session_state.get("image_roles") or None,
                        limit=s3_limit if s3_limit > 0 else None,
                        user_notes=user_notes.strip(),
                        log=lambda m: s.write(m),
                        progress=progress_cb,
                    )
                    st.session_state["stage3"] = plan_done
                    s.update(label="✅ Stage 3 completed", state="complete", expanded=False)
                except Exception as e:
                    s.update(label=f"❌ {e}", state="error", expanded=True)

    if st.session_state.get("stage3"):
        plan = st.session_state["stage3"]
        st.subheader("📝 Prompts ready")

        if "_files" in plan:
            c1, c2 = st.columns(2)
            with c1:
                jp = plan["_files"].get("prompts_json", "")
                st.markdown(f"📄 [Prompts JSON]({jp})")
            with c2:
                mp = plan["_files"].get("prompts_md", "")
                st.markdown(f"📝 [Prompts MD]({mp})")

        st.caption("💡 Every prompt is editable text. Changes are saved automatically and take effect when you click generate in Stage 4.")

        for idx, v in enumerate(plan.get("videos", [])):
            if not v.get("prompt"):
                continue
            vid = v.get("id")
            with st.expander(f"{vid} — {v.get('format_name')} ({v.get('duration_seconds')}s)"):
                edited = st.text_area(
                    "prompt",
                    v["prompt"],
                    height=240,
                    key=f"prompt_edit_{vid}",
                    label_visibility="collapsed",
                )
                # Save edits back to the plan structure
                if edited != v["prompt"]:
                    plan["videos"][idx]["prompt"] = edited
                    st.session_state["stage3"] = plan
                    st.caption(f"✓ Saved in memory (video {vid})")

    # Skip-stage-3 expander — accepts plain text (preferred) or JSON
    with st.expander("✏️ Option: skip Stage 3 — paste your own prompts", expanded=False):
        st.caption(
            "**The easy way:** paste each prompt separately, separated by a line with `===`. "
            "The file is created internally. **Advanced way:** paste JSON with `videos`."
        )
        manual_stage3 = st.text_area(
            "Prompts — separated by === (or JSON)",
            height=320,
            placeholder=(
                "Prompt #1 here — UGC video, 15 seconds...\n"
                "===\n"
                "Prompt #2 here — Hero shot, 10 seconds...\n"
                "===\n"
                "Prompt #3 here — Pattern interrupt...\n"
            ),
            key="manual_stage3_input",
            label_visibility="collapsed",
        )
        manual_dur = st.number_input(
            "Default duration per video (seconds)",
            min_value=5, max_value=30, value=int(default_duration), step=1,
            key="manual_stage3_dur",
        )
        if st.button("✅ Use the manual prompts (skip Stage 3)", key="use_manual_stage3"):
            text = manual_stage3.strip()
            if not text:
                st.error("You need to write prompts")
            else:
                # Try JSON first (advanced); if it fails, split by === (easy)
                new_plan = None
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict) and "videos" in parsed:
                        new_plan = parsed
                except Exception:
                    pass

                if new_plan is None:
                    # Plain text mode: split by === lines
                    chunks = [c.strip() for c in text.split("\n===\n") if c.strip()]
                    if len(chunks) == 1:  # No separators — try other variants
                        chunks = [c.strip() for c in text.split("===") if c.strip()]
                    videos = []
                    for i, prompt_text in enumerate(chunks, 1):
                        videos.append({
                            "id": i,
                            "format": 1,
                            "family": "Manual",
                            "format_name": "Manual prompt",
                            "duration_seconds": int(manual_dur),
                            "prompt": prompt_text,
                        })
                    new_plan = {
                        "campaign_name": campaign_name or "Manual prompts",
                        "total_videos": len(videos),
                        "videos": videos,
                    }

                videos_with_prompts = [v for v in new_plan.get("videos", []) if v.get("prompt")]
                if not videos_with_prompts:
                    st.error("No prompts found. Make sure prompts are separated with ===, or paste valid JSON.")
                else:
                    st.session_state["stage3"] = new_plan
                    # Stage 2 dummy so Stage 4 button works
                    if not st.session_state.get("stage2"):
                        st.session_state["stage2"] = new_plan
                    st.success(f"✓ Saved {len(videos_with_prompts)} prompts. Scroll to Stage 4 to generate.")
                    st.rerun()


    # ════════════════════════════════════════════════════════════
    # STAGE 4 — Render Videos via BytePlus
    # ════════════════════════════════════════════════════════════
st.header("5️⃣ Stage 4: Video generation (optional)")
st.caption("Sends the written prompts to Seedance and gets MP4s back. You can generate all of them or just some.")

# Reference audio (music / voiceover) — shared by Express + Full pipeline.
import ref_audio_helper as _ref_audio_mod
importlib.reload(_ref_audio_mod)
from ref_audio_helper import render_ref_audio_ui, get_ref_audio_urls
render_ref_audio_ui(PROJECT_ROOT)

# Recover orphaned tasks from previous session (Streamlit reload, network blip).
try:
    from task_queue import get_pending as _tq_pending, mark_done as _tq_done
    from byteplus_client import poll_task as _tq_poll, extract_video_url as _tq_xtract, download_video as _tq_dl
    _pending = _tq_pending(min_age_seconds=30)
    if _pending:
        st.warning(
            f"⚠ Found **{len(_pending)} tasks to collect** "
            f"from a previous session that were never downloaded (the session probably crashed mid-run). "
            f"You already paid for them — you can collect them without paying again."
        )
        if st.button(f"🔄 Collect the {len(_pending)} tasks now", key="resume_pending_btn"):
            with st.status("Collecting...", expanded=True) as _resume_status:
                for _t in _pending:
                    _tid = _t["task_id"]
                    _vid = _t.get("video_id", "?")
                    _ci = _t.get("chunk_idx", 1)
                    try:
                        _resume_status.write(f"📥 {_tid} (video #{_vid} chunk {_ci})...")
                        _result = _tq_poll(_tid, log=_resume_status.write)
                        _url = _tq_xtract(_result)
                        from datetime import datetime as _dt2
                        _ts = _dt2.now().strftime("%Y%m%d_%H%M%S")
                        _cp = OUTPUTS_DIR / "videos" / f"resumed_{_vid}_{_ts}_c{_ci}.mp4"
                        _cp.parent.mkdir(parents=True, exist_ok=True)
                        _tq_dl(_url, _cp)
                        _tq_done(_tid, output_path=str(_cp))
                        _resume_status.write(f"  ✓ {_cp.name}")
                    except Exception as _e:
                        _resume_status.write(f"  ❌ {_tid}: {_e}")
                _resume_status.update(label="✓ Done", state="complete")
            st.rerun()
except Exception:
    pass

s4_disabled = not st.session_state.get("stage3") or not IMGBB_API_KEY
videos_with_prompts = []
if st.session_state.get("stage3"):
    videos_with_prompts = [v for v in st.session_state["stage3"].get("videos", []) if v.get("prompt")]

# Track per-video success state across reruns
if "video_results" not in st.session_state:
    st.session_state["video_results"] = {}  # video_id -> Path

if videos_with_prompts:
    # Show per-video selector
    st.markdown(f"**{len(videos_with_prompts)} prompts ready** — pick which ones to generate:")

    # Quick action buttons
    qa1, qa2, qa3 = st.columns([1, 1, 1])
    with qa1:
        if st.button("✅ Select all", use_container_width=True, key="select_all_btn"):
            for v in videos_with_prompts:
                st.session_state[f"sel_{v['id']}"] = True
            st.rerun()
    with qa2:
        if st.button("⬜ Clear all", use_container_width=True, key="clear_all_btn"):
            for v in videos_with_prompts:
                st.session_state[f"sel_{v['id']}"] = False
            st.rerun()
    with qa3:
        if st.button("🔁 Only failed+missing", use_container_width=True, key="select_pending_btn",
                      help="Select only videos that have not been generated yet"):
            for v in videos_with_prompts:
                vid_id = v["id"]
                already_done = vid_id in st.session_state["video_results"]
                st.session_state[f"sel_{vid_id}"] = not already_done
            st.rerun()

    # Checkboxes per video — visual status
    selected_ids = []
    for v in videos_with_prompts:
        vid_id = v["id"]
        is_done = vid_id in st.session_state["video_results"]
        status_icon = "✅" if is_done else "⬜"
        label = f"{status_icon} {vid_id} — {v.get('format_name', '?')} ({v.get('duration_seconds', '?')}s)"

        # Default: pending videos checked, done videos unchecked
        default_state = not is_done
        # Use a stable session-state key per video
        sel_key = f"sel_{vid_id}"
        if sel_key not in st.session_state:
            st.session_state[sel_key] = default_state

        checked = st.checkbox(label, key=sel_key)
        if checked:
            selected_ids.append(vid_id)

    n_selected = len(selected_ids)
    st.info(f"💡 {n_selected} videos selected for generation (out of {len(videos_with_prompts)}). " +
             f"Cost: {n_selected} generations." if n_selected else "⚠️ No video selected for generation")

    if st.button(f"🎬 Generate {n_selected} selected videos",
                  type="primary",
                  disabled=s4_disabled or n_selected == 0,
                  use_container_width=True,
                  key="gen_videos_btn"):
            todo = [v for v in videos_with_prompts if v["id"] in selected_ids]
            video_outputs = []
            image_path = Path(st.session_state.get("image_path", ""))

            with st.status(f"🎬 Generating {len(todo)} videos on BytePlus...", expanded=True) as s4_status:
                try:
                    img_paths = [Path(ip) for ip in (st.session_state.get("image_paths") or []) if str(ip).strip()]
                    if img_paths:
                        s4_status.write(f"📤 Uploading {len(img_paths)} image(s) to imgbb (once)...")
                    else:
                        s4_status.write("ℹ No product images — continuing with prompt + reference video only.")
                    base_image_urls = []
                    for idx, ip in enumerate(img_paths, 1):
                        url = upload_image(ip)
                        base_image_urls.append(url)
                        s4_status.write(f"  ✓ Image {idx}: {ip.name}")
                    base_image_url = base_image_urls[0] if base_image_urls else None  # backward-compat

                    # Reference audio (Audio Studio voice + uploaded MP3s) — once per batch
                    ref_audio_urls = get_ref_audio_urls(log=s4_status.write)
                    if ref_audio_urls:
                        s4_status.write(f"🎵 {len(ref_audio_urls)} reference audio files will be attached (@Audio 1..{len(ref_audio_urls)})")

                    for vi, video in enumerate(todo, 1):
                        s4_status.write(f"\n━━━ Video {vi}/{len(todo)}: {video['id']} ({video.get('format_name')}) ━━━")
                        try:
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            duration = int(video.get("duration_seconds", 10))
                            ratio = video.get("aspect_ratio", "9:16")
                            resolution = video.get("resolution", "720p")

                            # Plan chunks: ≤15 = single, >15 = N×15s + remainder
                            # Seedance max per request = 15s, min per request = 5s
                            if duration <= 15:
                                chunk_durations = [duration]
                            else:
                                full_chunks = duration // 15
                                remainder = duration % 15
                                chunk_durations = [15] * full_chunks
                                if remainder >= 5:
                                    chunk_durations.append(remainder)
                                elif remainder > 0:
                                    chunk_durations[-1] = 15 - (5 - remainder)
                                    chunk_durations.append(5)
                            multi_chunk = len(chunk_durations) > 1

                            if multi_chunk and not is_ffmpeg_available():
                                s4_status.write(f"  ⚠ {video['id']} needs ffmpeg ({duration}s>15) — skipping")
                                continue

                            chunk_videos = []
                            chunk_prompts_used = []
                            for ci, chunk_dur in enumerate(chunk_durations, 1):
                                if multi_chunk:
                                    s4_status.write(f"  ━ Chunk {ci}/{len(chunk_durations)} ({chunk_dur}s) ━")

                                if ci == 1:
                                    chunk_image_urls = list(base_image_urls)
                                    from ref_video_helper import get_ref_video_urls
                                    chunk_video_refs = get_ref_video_urls(log=s4_status.write)
                                    chunk_audio_refs = list(ref_audio_urls)
                                    chunk_prompt = video["prompt"]
                                else:
                                    s4_status.write("  🔗 Extracting last frame...")
                                    last_frame_path = OUTPUTS_DIR / "videos" / f"_lf_{video['id']}_{ts}_c{ci-1}.jpg"
                                    extract_last_frame(chunk_videos[-1], last_frame_path)

                                    s4_status.write("  📤 Uploading the previous video to catbox.moe...")
                                    vid_url = upload_video(chunk_videos[-1])

                                    s4_status.write("  ✍️ Claude is writing a continuation...")
                                    continuation = pg.generate_continuation_prompt(
                                        opener_prompt=chunk_prompts_used[-1],
                                        brief=video.get("scene_summary", ""),
                                        image_paths=[Path(ip) for ip in st.session_state.get(
                                            "image_paths", [st.session_state["image_path"]])],
                                        video_path=chunk_videos[-1],
                                        last_frame_path=last_frame_path,
                                        target_duration=chunk_dur,
                                        brand_name=st.session_state.get("stage1", {}).get("product", {}).get("brand_name_visible", ""),
                                        log=s4_status.write,
                                    )
                                    chunk_image_urls = list(base_image_urls)
                                    chunk_video_refs = [vid_url]
                                    chunk_audio_refs = []  # audio refs go on the opener only
                                    chunk_prompt = continuation

                                chunk_prompts_used.append(chunk_prompt)

                                # Submit + poll with 1 retry on timeout
                                result = None
                                last_task_id = None
                                for attempt in range(2):
                                    attempt_label = "" if attempt == 0 else f" (retry {attempt})"
                                    s4_status.write(f"  📨 Sending chunk {ci}{attempt_label} to Seedance ({resolution}, {ratio}, {chunk_dur}s)...")
                                    task_id = submit_task(
                                        prompt=chunk_prompt,
                                        image_urls=chunk_image_urls,
                                        video_urls=chunk_video_refs,
                                        audio_urls=chunk_audio_refs,
                                        ratio=ratio,
                                        duration=chunk_dur,
                                        generate_audio=video.get("generate_audio", True),
                                        watermark=False,
                                        extra_payload={"resolution": resolution},
                                    )
                                    last_task_id = task_id
                                    try:
                                        from task_queue import add_task as _tq_add
                                        _tq_add(task_id, video_id=video["id"], chunk_idx=ci,
                                                total_chunks=len(chunk_durations),
                                                prompt=chunk_prompt, duration=chunk_dur,
                                                aspect_ratio=ratio)
                                    except Exception as _te:
                                        s4_status.write(f"    ⚠ task_queue.add_task failed: {_te}")
                                    s4_status.write(f"    task_id: {task_id}")
                                    s4_status.write("  ⏳ Waiting (up to 15 minutes)...")
                                    try:
                                        result = poll_task(task_id, log=s4_status.write)
                                        break  # success
                                    except TimeoutError as te:
                                        s4_status.write(f"  ⚠ timeout (attempt {attempt + 1}): {te}")
                                        if attempt == 0:
                                            s4_status.write("  🔄 Retrying once...")
                                        else:
                                            raise
                                if result is None:
                                    raise RuntimeError(f"Both attempts timed out for {video['id']} chunk {ci}")

                                video_url = extract_video_url(result)
                                cp = OUTPUTS_DIR / "videos" / f"{video['id']}_{ts}_c{ci}.mp4"
                                cp.parent.mkdir(parents=True, exist_ok=True)
                                download_video(video_url, cp)
                                chunk_videos.append(cp)
                                try:
                                    from task_queue import mark_done as _tq_done
                                    _tq_done(last_task_id, output_path=str(cp))
                                except Exception:
                                    pass
                                s4_status.write(f"  ✓ {cp.name}")

                            # Concat chunks if multi
                            if multi_chunk:
                                s4_status.write("  🪡 Stitching chunks into one MP4...")
                                out_path = OUTPUTS_DIR / "videos" / f"{video['id']}_{ts}_FULL_{duration}s.mp4"
                                concat_videos(chunk_videos, out_path)
                            else:
                                out_path = chunk_videos[0]

                            s4_status.write(f"  ✅ {out_path.name}")
                            video_outputs.append((video["id"], out_path))
                            # Save per-video to session_state so re-runs skip it
                            st.session_state["video_results"][video["id"]] = out_path
                        except Exception as ve:
                            s4_status.write(f"  ❌ {video['id']} failed: {ve}")

                    s4_status.update(
                        label=f"✅ Stage 4 completed — {len(video_outputs)}/{len(todo)} videos generated",
                        state="complete", expanded=False,
                    )
                    st.session_state["stage4"] = video_outputs
                except Exception as e:
                    s4_status.update(label=f"❌ {e}", state="error", expanded=True)


# ════════════════════════════════════════════════════════════
# 🎬 Generated Videos — view + download
# ════════════════════════════════════════════════════════════
if st.session_state.get("stage4"):
    st.markdown("---")
    st.header("🎬 Your generated videos")
    st.caption("Click ▶ to watch, or ⬇️ to download to your computer.")

    _outputs = st.session_state["stage4"]
    # Each entry can be (id, path) tuple or dict — normalize
    _normalized = []
    for item in _outputs:
        if isinstance(item, tuple):
            _normalized.append({"id": item[0], "path": str(item[1])})
        elif isinstance(item, dict):
            _normalized.append(item)

    _existing_vids = [Path(_it.get("path", "")) for _it in _normalized
                      if _it.get("path") and Path(_it.get("path", "")).exists()]
    if _existing_vids:
        import io as _io
        import zipfile as _zipf
        _buf = _io.BytesIO()
        with _zipf.ZipFile(_buf, "w", _zipf.ZIP_STORED) as _zf:
            for _p2 in _existing_vids:
                _zf.write(_p2, _p2.name)
            _plan3 = st.session_state.get("stage3") or {}
            _txt = "\n\n".join(
                f"=== Video {v.get('id')} ({v.get('duration_seconds')}s) ===\n{v.get('prompt', '')}"
                for v in _plan3.get("videos", []) if v.get("prompt"))
            if _txt:
                _zf.writestr("prompts.txt", _txt)
        st.download_button(
            f"📦 Download CapCut editing package ({len(_existing_vids)} videos + prompts)",
            _buf.getvalue(), file_name="capcut_package.zip", mime="application/zip",
            use_container_width=True, key="capcut_zip_btn",
        )
        st.caption(
            "Extract the ZIP → in CapCut: New project → Import → select all the files. "
            "Each video goes into the timeline as a separate clip, and prompts.txt helps with captions."
        )

    if not _normalized:
        st.info("No videos available to display.")
    else:
        _cols_per_row = 2
        for i in range(0, len(_normalized), _cols_per_row):
            _row = _normalized[i:i + _cols_per_row]
            _cols = st.columns(len(_row))
            for _col, _item in zip(_cols, _row):
                with _col:
                    _vid_id = _item.get("id", "?")
                    _path = Path(_item.get("path", ""))
                    if _path.exists():
                        st.markdown(f"**Video #{_vid_id}** · {_path.name}")
                        with open(_path, "rb") as _f:
                            _bytes = _f.read()
                        st.video(_bytes)
                        st.download_button(
                            label=f"⬇️ Download video #{_vid_id}",
                            data=_bytes,
                            file_name=_path.name,
                            mime="video/mp4",
                            key=f"dl_video_{_vid_id}_{_path.name}",
                            use_container_width=True,
                        )
                        _size_mb = len(_bytes) / 1024 / 1024
                        st.caption(f"{_size_mb:.1f} MB")
                    else:
                        st.warning(f"Video #{_vid_id} not found on disk.")


# ════════════════════════════════════════════════════════════
# 📂 All videos on the server — file browser + ZIP bulk download
# ════════════════════════════════════════════════════════════
# Even after a session reset, the user can grab any MP4 still sitting on the
# Streamlit Cloud VM's disk. Lists all *.mp4 in outputs/videos/, newest first.
st.markdown("---")
with st.expander("📂 All videos stored on the server — direct file access", expanded=False):
    st.caption(
        "⚠ Files are stored on Streamlit Cloud temporarily only. "
        "When the VM restarts (rebuild, long inactivity) they are deleted. "
        "**Download them to your computer for long-term storage.**"
    )

    _videos_dir = OUTPUTS_DIR / "videos"
    if not _videos_dir.exists():
        st.info("No videos created yet. After you generate in Stage 4, they will appear here.")
    else:
        _all_mp4s = sorted(
            _videos_dir.glob("*.mp4"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not _all_mp4s:
            st.info("The folder is empty — no videos created yet.")
        else:
            from datetime import datetime as _dt
            _total_size = sum(p.stat().st_size for p in _all_mp4s)
            st.success(
                f"✓ {len(_all_mp4s)} files on the server · "
                f"total {_total_size / 1024 / 1024:.1f} MB"
            )
            st.info(
                "💡 **Note:** Streamlit's direct download sometimes stalls on large files. "
                "Instead, click '📤 Create permanent link' next to each video — it is uploaded to catbox "
                "(a public, stable link with its own CDN), and you get a link you can open in a new tab "
                "and download directly from the browser with no issues."
            )

            # Cache uploaded URLs per file in session_state
            _url_cache = st.session_state.setdefault("_video_share_urls", {})

            # ── Bulk upload all → returns a list of shareable links ──
            if st.button(
                f"\U0001F4E4 Create download links for all {len(_all_mp4s)} videos",
                type="primary",
                use_container_width=True,
                key="upload_all_btn",
                help="Uploads each video to catbox (a permanent link). Takes a few seconds per video.",
            ):
                _prog = st.progress(0.0, text="Uploading...")
                for _i, _p in enumerate(_all_mp4s):
                    if str(_p) not in _url_cache:
                        try:
                            _url_cache[str(_p)] = upload_video(_p)
                        except Exception as _e:
                            st.warning(f"\u274C {_p.name}: {_e}")
                    _prog.progress((_i + 1) / len(_all_mp4s), text=f"Uploading {_i+1}/{len(_all_mp4s)}: {_p.name}")
                _prog.empty()
                st.success(f"\u2713 Uploaded {len(_url_cache)} videos. The links appear below.")
                st.rerun()

            st.markdown("---")
            st.markdown(f"**\U0001F4CB File list** (newest \u2192 oldest):")

            # Per-file row: name, mtime, size, action button
            for _p in _all_mp4s:
                _mtime = _dt.fromtimestamp(_p.stat().st_mtime)
                _size_mb = _p.stat().st_size / 1024 / 1024
                _cols = st.columns([3, 2, 1, 2, 1])
                # 🗑 delete with two-step confirm (paid generations — no accidents)
                with _cols[4]:
                    _del_key = f"delask_{_p.name}"
                    if st.session_state.get(_del_key):
                        if st.button("✔ Delete", key=f"delok_{_p.name}",
                                      type="primary", use_container_width=True,
                                      help="Permanently delete from the server"):
                            try:
                                _p.unlink()
                                _url_cache.pop(str(_p), None)
                                st.session_state.pop(_del_key, None)
                                st.rerun()
                            except Exception as _de:
                                st.error(f"Delete failed: {_de}")
                        if st.button("✖ Cancel", key=f"delno_{_p.name}",
                                      use_container_width=True):
                            st.session_state.pop(_del_key, None)
                            st.rerun()
                    else:
                        if st.button("🗑", key=f"delbtn_{_p.name}",
                                      use_container_width=True,
                                      help="Remove the video from the server"):
                            st.session_state[_del_key] = True
                            st.rerun()
                with _cols[0]:
                    st.text(_p.name)
                with _cols[1]:
                    st.caption(_mtime.strftime("%Y-%m-%d %H:%M:%S"))
                with _cols[2]:
                    st.caption(f"{_size_mb:.1f} MB")
                with _cols[3]:
                    _key = str(_p)
                    if _key in _url_cache:
                        st.link_button(
                            "\u2B07\ufe0f Download from catbox",
                            _url_cache[_key],
                            use_container_width=True,
                            help="Right-click \u2192 'Save link as...' or open in a new tab",
                        )
                    else:
                        if st.button(
                            "\U0001F4E4 Create permanent link",
                            key=f"upload_one_{_p.name}",
                            use_container_width=True,
                            help="Uploads to catbox and creates a direct download link",
                        ):
                            with st.spinner(f"Uploading {_p.name}..."):
                                try:
                                    _url_cache[_key] = upload_video(_p)
                                    st.rerun()
                                except Exception as _e:
                                    st.error(f"Upload error: {_e}")
