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
            st.write("Anthropic API מוגדר. ירוץ Claude דרך ה-API (cloud mode).")
        else:
            st.warning("חסר ANTHROPIC_API_KEY ב-Streamlit Secrets")
            st.write("השג ב-https://console.anthropic.com/")

    # Gemini
    title = f"{'✅' if GEMINI_API_KEY else '⚠️'} Gemini Vision + Nano Banana 2"
    with st.expander(title, expanded=False):
        if GEMINI_API_KEY:
            st.write("משמש ל-2 דברים:")
            st.write("1. **Stage 1**: זיהוי קטגוריית מוצר אוטומטית מתמונה")
            st.write("2. **Nano Banana 2**: יצירת תמונות סצנה (אופציונלי)")
        else:
            st.warning("חסר GEMINI_API_KEY ב-.env")
            st.write("השג חינם ב-https://aistudio.google.com/apikey")

    # Tavily
    title = f"{'✅' if TAVILY_API_KEY else '⚠️'} Tavily web search"
    with st.expander(title, expanded=False):
        if TAVILY_API_KEY:
            st.write("רץ 8 חיפושי אינטרנט כדי לאסוף טרנדים בנישה של המוצר.")
        else:
            st.warning("חסר TAVILY_API_KEY ב-.env")
            st.write("השג ב-https://tavily.com/")

    # imgbb
    title = f"{'✅' if IMGBB_API_KEY else '⚠️'} imgbb image hosting"
    with st.expander(title, expanded=False):
        if IMGBB_API_KEY:
            st.write("מעלה תמונות מוצר לשרת ציבורי כדי ש-BytePlus יוכל למשוך.")
        else:
            st.warning("חסר IMGBB_API_KEY ב-.env")

    # ffmpeg
    title = f"{'✅' if is_ffmpeg_available() else '⚠️'} ffmpeg ready"
    with st.expander(title, expanded=False):
        if is_ffmpeg_available():
            st.write("ffmpeg זמין דרך imageio-ffmpeg.")
            st.write("משמש ל: חילוץ פריים אחרון + הדבקת chunks לוידאו ארוך.")
        else:
            st.warning("ffmpeg חסר. הרץ 1_SETUP.bat שוב.")

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
    st.header("1️⃣ העלה תמונות מוצר + בחר פרמטרים")
    st.caption("מעלים 1-9 תמונות (מוצר, צבעים, רכיבים, זוויות) — כל תמונה תהפוך ל-@Image שאפשר להראות בסרטון.")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        uploaded_files = st.file_uploader(
            "תמונות מוצר (עד 9 — הראשונה = Image 1, השנייה = Image 2 וכו')",
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
                    "🏷 **תפקיד לכל תמונה (מומלץ!)** — קלוד ישתמש בזה כדי לשלב "
                    "את כל המוצרים/הרכיבים נכון בסרטון אחד (@Image 1, @Image 2...)."
                )
                image_roles = []
                role_cols = st.columns(min(len(image_paths), 3))
                for idx, ip in enumerate(image_paths):
                    with role_cols[idx % 3]:
                        role = st.text_input(
                            f"@Image {idx+1}",
                            key=f"img_role_{idx}",
                            placeholder="למשל: בקבוק - חזית / כף מדידה / האריזה מאחור",
                        )
                        image_roles.append(role.strip())
                st.session_state["image_roles"] = image_roles
            else:
                st.session_state["image_roles"] = []

    with col_b:
        sub_a, sub_b = st.columns(2)
        with sub_a:
            total_videos = st.selectbox(
                "כמה וידאו ליצור?",
                [1, 3, 5, 10, 20, 50, 100, 200],
                index=2,
                help="התפלגות אוטומטית: 1=Product Review, 5=מגוון פורמטים, 100+=כל 23 הפורמטים",
            )
            default_duration = st.selectbox(
                "משך ברירת מחדל (שניות)",
                [5, 8, 10, 15, 20, 25, 30],
                index=3,
                format_func=lambda x: f"{x}s" + (" (×2 chunks)" if x > 15 else ""),
                help="≤15s = generation בודד. 20-30s = שני chunks (opener+continuation) שמודבקים אוטומטית עם ffmpeg.",
            )
            duration_policy = st.radio(
                "מדיניות משך",
                ["Strict — תמיד המשך שלי", "Flexible — מותר לקלוד להציע אחרת לפי הפורמט/המחקר"],
                index=1,
                help="Strict: כל הוידאו יהיו במשך שבחרת. Flexible: אם המחקר ממליץ על 25s ל-Storytime, Claude יכתוב 25s ונייצר 2 chunks."
            )
            max_duration = st.selectbox(
                "מקסימום מותר (Flexible mode)",
                [15, 20, 25, 30],
                index=3,
                help="ב-Flexible — קלוד יכול להגיע עד לסף הזה. מעל 15s = multi-chunk."
            )
            audience = st.selectbox(
                "קהל יעד",
                ["American", "Israeli", "Pan-Arab / MENA", "Slavic / CIS",
                 "East Asian", "Latin American", "Mixed international"],
                index=0,
                help="דורס את הזיהוי האוטומטי של Gemini. השפעה: heritage של הדמויות, סביבה (American kitchen/gym/etc.), accent.",
            )
        with sub_b:
            campaign_name = st.text_input("שם קמפיין (אופציונלי)", placeholder="auto-generated")
            date_range = st.selectbox("טווח תאריכים", ["30 days", "60 days", "90 days", "no dates"])
            brand_input = st.text_input("שם המותג (אופציונלי, דורס את הזיהוי)", placeholder="auto-detected from packaging")

    # Notes — free-form context that affects all 3 stages
    st.markdown("**💬 הערות חופשיות (אופציונלי) — מועבר לכל שלב**")
    user_notes = st.text_area(
        "כל מידע נוסף שיעזור לקלוד לדייק את הקמפיין",
        height=120,
        placeholder=(
            "לדוגמה:\n"
            "- קהל יעד מדויק: נשים 40-60 עם כאבי גב/רגליים\n"
            "- המוצר מומלץ ע\"י אורתופדים, לא רק כאב כללי\n"
            "- אנחנו מוכרים ב-Amazon US בעיקר, פחות ב-DTC\n"
            "- להימנע מטענות רפואיות (FDA compliance)\n"
            "- הנקודה הכי חזקה: הקלה מורגשת תוך 3 ימים\n"
            "- אסור להזכיר מתחרים\n"
        ),
        help="הטקסט הזה יישלח לקלוד בכל שלב — Stage 1 (brief), Stage 2 (plan), Stage 3 (prompts). פרטים יותר → דיוק יותר.",
        label_visibility="collapsed",
    )


    # ════════════════════════════════════════════════════════════
    # STAGE 1 — Research
    # ════════════════════════════════════════════════════════════
    st.header("2️⃣ שלב 1: מחקר טרנדים + ניתוח מוצר")

    # LLM is available if Chrome+CDP is up locally OR the Anthropic API key is set (cloud).
    try:
        from anthropic_client import is_available as _anthropic_ok
        llm_ok = chrome_ok or _anthropic_ok()
    except Exception:
        llm_ok = chrome_ok
    s1_disabled = not st.session_state.get("image_path") or not llm_ok or not GEMINI_API_KEY or not TAVILY_API_KEY
    if st.button("🔍 הרץ Stage 1 — Research", type="primary", disabled=s1_disabled,
                  help="חייב: תמונה + (Chrome או Anthropic API) + Gemini + Tavily" if s1_disabled else None):
        with st.status("🔍 Stage 1 בריצה...", expanded=True) as s:
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
                s.write("🤖 קלוד בוחר פורמטים אופטימליים מהמחקר (אוטומטית)...")
                try:
                    smart_split = stage1_runner.recommend_formats_from_research(
                        stage1_result=result,
                        total_videos=total_videos,
                        enabled_format_pool=list(ALL_FORMATS.keys()),
                        user_notes=user_notes.strip(),
                        log=lambda m: s.write(m),
                    )
                    st.session_state["smart_pick"] = smart_split
                    s.write(f"✓ Smart Pick: {len(smart_split)} פורמטים נבחרו לפי המחקר")
                except Exception as sp_e:
                    s.write(f"⚠ Smart Pick נכשל ({sp_e}) — נסה ידנית אחרי שלב 1")
                s.update(label="✅ Stage 1 + Smart Pick הושלמו", state="complete", expanded=False)
            except Exception as e:
                s.update(label=f"❌ {e}", state="error", expanded=True)

    if st.session_state.get("stage1"):
        s1 = st.session_state["stage1"]
        with st.expander("📦 Product Profile (auto-detected)", expanded=False):
            # Editable product JSON
            prod_text = st.text_area(
                "ערוך פרטי מוצר (JSON)",
                value=json.dumps(s1["product"], indent=2, ensure_ascii=False),
                height=260,
                key="product_edit",
            )
            if st.button("💾 שמור פרטי מוצר", key="save_product"):
                try:
                    s1["product"] = json.loads(prod_text)
                    st.session_state["stage1"] = s1
                    st.success("✓ נשמר")
                except Exception as e:
                    st.error(f"JSON לא תקין: {e}")

        with st.expander("📄 Viral Content Brief — ניתן לעריכה ידנית", expanded=True):
            brief_edited = st.text_area(
                "ערוך את ה-Brief — כל מה שתשנה כאן ישפיע על שלב 2",
                value=s1["viral_brief"],
                height=400,
                key="brief_edit",
                label_visibility="collapsed",
            )
            if st.button("💾 שמור Brief", key="save_brief"):
                s1["viral_brief"] = brief_edited
                st.session_state["stage1"] = s1
                st.success("✓ Brief נשמר. שלב 2 ישתמש בגרסה החדשה.")

    # Skip-stage-1 expander: paste your own brief
    with st.expander("✏️ אופציה: דלג על Stage 1 — כתוב Brief משלך", expanded=False):
        st.caption("אם יש לך Brief מוכן ואתה לא צריך מחקר — הדבק כאן והמשך לשלב 2.")
        manual_brief = st.text_area(
            "Brief ידני",
            height=300,
            placeholder="פסקה 1: למה הבעיה הזאת בוערת לקהל...\nפסקה 2: הזוויות הוויראליות...\nפסקה 3: יסודות יצירתיים...",
            key="manual_brief_input",
            label_visibility="collapsed",
        )
        manual_product_json = st.text_area(
            "פרטי מוצר ידניים (JSON) — אופציונלי, אם לא מילאת קלוד לא יידע מה זה",
            value='{\n  "category": "",\n  "subtype": "",\n  "skus_visible": [],\n  "brand_name_visible": "",\n  "packaging_colors": [],\n  "packaging_style": "",\n  "region_cue": "global",\n  "niche_keyword": "",\n  "audience_default": "American"\n}',
            height=240,
            key="manual_product_input",
        )
        if st.button("✅ השתמש בקלט הידני (דלג על Stage 1)", key="use_manual_brief"):
            if not manual_brief.strip():
                st.error("צריך לכתוב Brief")
            else:
                try:
                    manual_product = json.loads(manual_product_json) if manual_product_json.strip() else {}
                    st.session_state["stage1"] = {
                        "product": manual_product,
                        "viral_brief": manual_brief.strip(),
                        "research": {"manual": True},
                    }
                    st.success("✓ Stage 1 ידני נשמר. תוכל להמשיך לשלב 2.")
                    st.rerun()
                except Exception as e:
                    st.error(f"JSON של פרטי מוצר לא תקין: {e}")


    # ════════════════════════════════════════════════════════════
    # Format selection — AFTER Stage 1, auto-picked by research
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    with st.expander(f"🎯 בחירת פורמטים ({total_videos} וידאו) — לראות / לעקוף את הבחירה האוטומטית", expanded=False):
        # Compute the auto-picked formats
        auto_split = compute_format_split(total_videos, list(ALL_FORMATS.keys()))
        auto_picked = sorted([f for f, c in auto_split.items() if c > 0], key=lambda f: -auto_split.get(f, 0))

        # SMART PICK button — uses research from Stage 1 to let Claude decide
        smart_disabled = not st.session_state.get("stage1") or not llm_ok
        smart_help = (
            "חייב להריץ קודם Stage 1 (כדי שיהיה לקלוד מחקר לעבוד איתו) + Chrome פעיל"
            if smart_disabled else
            "קלוד יבחר פורמטים מבוססי המחקר והמוצר הספציפי — לא priority גנרי"
        )
        if st.button("🤖 Smart Pick — תן לקלוד לבחור לפי המחקר",
                      disabled=smart_disabled, help=smart_help, use_container_width=True):
            with st.spinner("קלוד בוחר פורמטים אופטימליים מהמחקר..."):
                try:
                    smart_split = stage1_runner.recommend_formats_from_research(
                        stage1_result=st.session_state["stage1"],
                        total_videos=total_videos,
                        enabled_format_pool=list(ALL_FORMATS.keys()),
                        user_notes=user_notes.strip(),
                        log=lambda m: st.write(m),
                    )
                    st.session_state["smart_pick"] = smart_split
                    st.success(f"✅ Smart pick: {sum(smart_split.values())} וידאו, {len(smart_split)} פורמטים")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Smart Pick נכשל: {e}")

        # Decide which split to display as default in the multiselect
        if st.session_state.get("smart_pick"):
            smart = st.session_state["smart_pick"]
            default_pool = sorted(smart.keys(), key=lambda f: -smart.get(f, 0))
            st.markdown(f"**Smart Pick מ-Claude (מבוסס מחקר):** {len(default_pool)} פורמטים")
            for fn, cnt in smart.items():
                st.caption(f"  - Format #{fn} {ALL_FORMATS[fn][2]}: ×{cnt}")
            st.markdown("")
            st.markdown(f"**אפשר לערוך** ({len(auto_picked)} ב-priority הגנרי, או Smart Pick למעלה):")
            default_selection = default_pool
        else:
            st.markdown(f"**ברירת מחדל אוטומטית** ({len(auto_picked)} פורמטים נבחרו לפי priority):")
            default_selection = auto_picked.copy()
    

        # Format label helper
        def fmt_label(f_num):
            name, fam, display = ALL_FORMATS[f_num]
            count = auto_split.get(f_num, 0)
            return f"[Family {fam}] #{f_num} {display}" + (f"  ×{count}" if count > 0 else "")

        # Show all 23 with the chosen pre-selection
        all_format_options = list(ALL_FORMATS.keys())

        selected_formats = st.multiselect(
            "פורמטים לכלול בקמפיין",
            options=all_format_options,
            default=default_selection,
            format_func=fmt_label,
            help="ברירת מחדל = הבחירה האוטומטית. הוסף/הסר כרצונך. אם תבחר פחות פורמטים ממספר הוידאו, חלקם יקבלו יותר מאחד."
        )

        if selected_formats:
            manual_split = compute_format_split(total_videos, selected_formats)
            active_split = {k: v for k, v in manual_split.items() if v > 0}
            st.info(f"💡 תקבל **{sum(active_split.values())} וידאו ב-{len(active_split)} פורמטים**: " +
                    ", ".join(f"{ALL_FORMATS[f][2]} ×{c}" for f, c in active_split.items()))
            # Save the selection so Stage 2 uses it
            st.session_state["selected_formats"] = selected_formats
        else:
            st.warning("⚠️ לא נבחרו פורמטים — Stage 1 יתבסס על הברירת מחדל האוטומטית")
            st.session_state["selected_formats"] = None


    # ════════════════════════════════════════════════════════════
    # STAGE 2 — Plan
    # ════════════════════════════════════════════════════════════
    st.header("3️⃣ שלב 2: תכנית קמפיין")

    s2_disabled = not st.session_state.get("stage1") or not llm_ok
    if st.button("🗂 הרץ Stage 2 — Plan", type="primary", disabled=s2_disabled):
        with st.status("🗂 Stage 2 בריצה...", expanded=True) as s:
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
                s.update(label=f"✅ Stage 2 הושלם — {len(plan.get('videos', []))} שורות בתכנית",
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
        with st.expander("✏️ ערוך תכנית ידנית (JSON) — שינויים ישפיעו על שלב 3", expanded=False):
            plan_text = st.text_area(
                "Plan JSON",
                value=json.dumps(plan, indent=2, ensure_ascii=False),
                height=500,
                key="plan_edit",
                label_visibility="collapsed",
            )
            if st.button("💾 שמור תכנית", key="save_plan"):
                try:
                    new_plan = json.loads(plan_text)
                    st.session_state["stage2"] = new_plan
                    st.success(f"✓ תכנית נשמרה — {len(new_plan.get('videos', []))} וידאו")
                    st.rerun()
                except Exception as e:
                    st.error(f"JSON לא תקין: {e}")

    # Skip-stage-2 expander
    with st.expander("✏️ אופציה: דלג על Stage 2 — כתוב תכנית משלך", expanded=False):
        st.caption("אם יש לך תכנית מוכנה (JSON עם השדה videos) — הדבק כאן.")
        manual_plan = st.text_area(
            "תכנית ידנית",
            height=320,
            placeholder='{\n  "campaign_name": "...",\n  "videos": [\n    {"id": 1, "format": 1, "family": "UGC", "format_name": "...", "duration_seconds": 15, "setting": "...", "persona": "...", "hook_line": "..."}\n  ]\n}',
            key="manual_plan_input",
            label_visibility="collapsed",
        )
        if st.button("✅ השתמש בתכנית הידנית (דלג על Stage 2)", key="use_manual_plan"):
            if not manual_plan.strip():
                st.error("צריך לכתוב תכנית")
            else:
                try:
                    new_plan = json.loads(manual_plan)
                    if "videos" not in new_plan:
                        st.error("חייב להיות שדה 'videos'")
                    else:
                        st.session_state["stage2"] = new_plan
                        st.success(f"✓ תכנית ידנית נשמרה — {len(new_plan.get('videos', []))} וידאו")
                        st.rerun()
                except Exception as e:
                    st.error(f"JSON לא תקין: {e}")


    # ════════════════════════════════════════════════════════════
    # STAGE 3 — Prompts
    # ════════════════════════════════════════════════════════════
    st.header("4️⃣ שלב 3: כתיבת פרומטים לכל וידאו")

    s3_disabled = not st.session_state.get("stage2") or not llm_ok
    col_s3a, col_s3b = st.columns([1, 3])
    with col_s3a:
        s3_limit = st.number_input("הגבל למספר וידאו ראשונים (0=הכל)",
                                    min_value=0, max_value=200, value=0, step=1,
                                    help="לבדיקה: נסה רק 2-3 לפני שמייצרים הכל")
    with col_s3b:
        if st.button("✍️ הרץ Stage 3 — Prompts", type="primary", disabled=s3_disabled, use_container_width=True):
            with st.status("✍️ Stage 3 בריצה (זמן: ~30s לכל וידאו)...", expanded=True) as s:
                try:
                    plan = dict(st.session_state["stage2"])  # mutable copy
                    product = st.session_state["stage1"]["product"]
                    image_path = Path(st.session_state["image_path"])

                    progress_bar = s.progress(0.0)
                    def progress_cb(i, total):
                        progress_bar.progress(i / total, text=f"וידאו {i}/{total}")

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
                    s.update(label="✅ Stage 3 הושלם", state="complete", expanded=False)
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

        st.caption("💡 כל פרומט הוא טקסט לעריכה. שינויים נשמרים אוטומטית ויופעלו כשתלחץ על 'ייצור הוידאו' בשלב 4.")

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
                    st.caption(f"✓ נשמר ב-זיכרון (וידאו {vid})")

    # Skip-stage-3 expander — accepts plain text (preferred) or JSON
    with st.expander("✏️ אופציה: דלג על Stage 3 — הדבק פרומטים משלך", expanded=False):
        st.caption(
            "**הדרך הקלה:** הדבק כל פרומט בנפרד, מופרדים על ידי שורה עם `===`. "
            "אני אצור את הקובץ פנימית. **דרך מתקדמת:** הדבק JSON עם `videos`."
        )
        manual_stage3 = st.text_area(
            "פרומטים — מופרדים על ידי === (או JSON)",
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
            "משך ברירת מחדל לכל וידאו (שניות)",
            min_value=5, max_value=30, value=int(default_duration), step=1,
            key="manual_stage3_dur",
        )
        if st.button("✅ השתמש בפרומטים הידניים (דלג על Stage 3)", key="use_manual_stage3"):
            text = manual_stage3.strip()
            if not text:
                st.error("צריך לכתוב פרומטים")
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
                    st.error("לא מצאתי אף פרומט. ודא שאתה מפריד עם === בין פרומטים, או מדביק JSON תקין.")
                else:
                    st.session_state["stage3"] = new_plan
                    # Stage 2 dummy so Stage 4 button works
                    if not st.session_state.get("stage2"):
                        st.session_state["stage2"] = new_plan
                    st.success(f"✓ נשמרו {len(videos_with_prompts)} פרומטים. גלול ל-Stage 4 לייצור.")
                    st.rerun()


    # ════════════════════════════════════════════════════════════
    # STAGE 4 — Render Videos via BytePlus
    # ════════════════════════════════════════════════════════════
st.header("5️⃣ שלב 4: ייצור הוידאו (אופציונלי)")
st.caption("שולח את הפרומטים שנכתבו לסידנס, מקבל MP4. ניתן ליצור הכל או רק חלק.")

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
            f"⚠ נמצאו **{len(_pending)} משימות שיש לאסוף** "
            f"מסשן קודם שלא הורדנו (כנראה הסשן נפל באמצע). "
            f"שילמת עליהן — אפשר לאסוף אותן בלי לשלם שוב."
        )
        if st.button(f"🔄 אסוף עכשיו את {len(_pending)} המשימות", key="resume_pending_btn"):
            with st.status("מאסף...", expanded=True) as _resume_status:
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
                _resume_status.update(label="✓ סיום", state="complete")
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
    st.markdown(f"**{len(videos_with_prompts)} פרומטים מוכנים** — בחר אילו לייצר:")

    # Quick action buttons
    qa1, qa2, qa3 = st.columns([1, 1, 1])
    with qa1:
        if st.button("✅ סמן הכל", use_container_width=True, key="select_all_btn"):
            for v in videos_with_prompts:
                st.session_state[f"sel_{v['id']}"] = True
            st.rerun()
    with qa2:
        if st.button("⬜ נקה הכל", use_container_width=True, key="clear_all_btn"):
            for v in videos_with_prompts:
                st.session_state[f"sel_{v['id']}"] = False
            st.rerun()
    with qa3:
        if st.button("🔁 רק נכשלים+חסרים", use_container_width=True, key="select_pending_btn",
                      help="סמן רק וידאו שעוד לא נוצרו"):
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
    st.info(f"💡 {n_selected} וידאו מסומנים לייצור (מתוך {len(videos_with_prompts)}). " +
             f"עלות: {n_selected} generations." if n_selected else "⚠️ לא נבחר וידאו לייצור")

    if st.button(f"🎬 צור {n_selected} וידאו מסומנים",
                  type="primary",
                  disabled=s4_disabled or n_selected == 0,
                  use_container_width=True,
                  key="gen_videos_btn"):
            todo = [v for v in videos_with_prompts if v["id"] in selected_ids]
            video_outputs = []
            image_path = Path(st.session_state.get("image_path", ""))

            with st.status(f"🎬 מייצר {len(todo)} וידאו ב-BytePlus...", expanded=True) as s4_status:
                try:
                    img_paths = [Path(ip) for ip in (st.session_state.get("image_paths") or []) if str(ip).strip()]
                    if img_paths:
                        s4_status.write(f"📤 מעלה {len(img_paths)} תמונה/ות ל-imgbb (פעם אחת)...")
                    else:
                        s4_status.write("ℹ אין תמונות מוצר — ממשיך עם prompt + reference video בלבד.")
                    base_image_urls = []
                    for idx, ip in enumerate(img_paths, 1):
                        url = upload_image(ip)
                        base_image_urls.append(url)
                        s4_status.write(f"  ✓ Image {idx}: {ip.name}")
                    base_image_url = base_image_urls[0] if base_image_urls else None  # backward-compat

                    # Reference audio (Audio Studio voice + uploaded MP3s) — once per batch
                    ref_audio_urls = get_ref_audio_urls(log=s4_status.write)
                    if ref_audio_urls:
                        s4_status.write(f"🎵 {len(ref_audio_urls)} רפרנס אודיו יצורפו (@Audio 1..{len(ref_audio_urls)})")

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
                                s4_status.write(f"  ⚠ {video['id']} צריך ffmpeg ({duration}s>15) — מדלג")
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
                                    s4_status.write("  🔗 מחלץ פריים אחרון...")
                                    last_frame_path = OUTPUTS_DIR / "videos" / f"_lf_{video['id']}_{ts}_c{ci-1}.jpg"
                                    extract_last_frame(chunk_videos[-1], last_frame_path)

                                    s4_status.write("  📤 מעלה Video הקודם ל-catbox.moe...")
                                    vid_url = upload_video(chunk_videos[-1])

                                    s4_status.write("  ✍️ קלוד כותב continuation...")
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
                                    s4_status.write(f"  📨 שולח chunk {ci}{attempt_label} ל-Seedance ({resolution}, {ratio}, {chunk_dur}s)...")
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
                                    s4_status.write("  ⏳ ממתין (עד 15 דקות)...")
                                    try:
                                        result = poll_task(task_id, log=s4_status.write)
                                        break  # success
                                    except TimeoutError as te:
                                        s4_status.write(f"  ⚠ timeout (attempt {attempt + 1}): {te}")
                                        if attempt == 0:
                                            s4_status.write("  🔄 מנסה שוב פעם אחת...")
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
                                s4_status.write("  🪡 מדביק chunks ל-MP4 אחד...")
                                out_path = OUTPUTS_DIR / "videos" / f"{video['id']}_{ts}_FULL_{duration}s.mp4"
                                concat_videos(chunk_videos, out_path)
                            else:
                                out_path = chunk_videos[0]

                            s4_status.write(f"  ✅ {out_path.name}")
                            video_outputs.append((video["id"], out_path))
                            # Save per-video to session_state so re-runs skip it
                            st.session_state["video_results"][video["id"]] = out_path
                        except Exception as ve:
                            s4_status.write(f"  ❌ {video['id']} נכשל: {ve}")

                    s4_status.update(
                        label=f"✅ Stage 4 הושלם — {len(video_outputs)}/{len(todo)} וידאו נוצרו",
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
    st.header("🎬 הוידאו שיצרת")
    st.caption("לחץ ▶ לצפייה, או ⬇️ להוריד למחשב.")

    _outputs = st.session_state["stage4"]
    # Each entry can be (id, path) tuple or dict — normalize
    _normalized = []
    for item in _outputs:
        if isinstance(item, tuple):
            _normalized.append({"id": item[0], "path": str(item[1])})
        elif isinstance(item, dict):
            _normalized.append(item)

    if not _normalized:
        st.info("אין וידאו זמינים להצגה.")
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
                        st.markdown(f"**וידאו #{_vid_id}** · {_path.name}")
                        with open(_path, "rb") as _f:
                            _bytes = _f.read()
                        st.video(_bytes)
                        st.download_button(
                            label=f"⬇️ הורד וידאו #{_vid_id}",
                            data=_bytes,
                            file_name=_path.name,
                            mime="video/mp4",
                            key=f"dl_video_{_vid_id}_{_path.name}",
                            use_container_width=True,
                        )
                        _size_mb = len(_bytes) / 1024 / 1024
                        st.caption(f"{_size_mb:.1f} MB")
                    else:
                        st.warning(f"וידאו #{_vid_id} לא נמצא בדיסק.")


# ════════════════════════════════════════════════════════════
# 📂 כל הוידאו על השרת — file browser + ZIP bulk download
# ════════════════════════════════════════════════════════════
# Even after a session reset, the user can grab any MP4 still sitting on the
# Streamlit Cloud VM's disk. Lists all *.mp4 in outputs/videos/, newest first.
st.markdown("---")
with st.expander("📂 כל הוידאו ששמורים על השרת — גישה ישירה לקבצים", expanded=False):
    st.caption(
        "⚠ הקבצים נשמרים על Streamlit Cloud באופן זמני בלבד. "
        "כשה-VM מאתחל (חידוש בנייה, חוסר פעילות ממושך) הם נמחקים. "
        "**הורד אותם למחשב שלך כדי לשמור לטווח ארוך.**"
    )

    _videos_dir = OUTPUTS_DIR / "videos"
    if not _videos_dir.exists():
        st.info("עוד לא נוצרו וידאו. אחרי שתייצר ב-Stage 4, הם יופיעו כאן.")
    else:
        _all_mp4s = sorted(
            _videos_dir.glob("*.mp4"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not _all_mp4s:
            st.info("התיקייה ריקה — עדיין לא נוצרו וידאו.")
        else:
            from datetime import datetime as _dt
            _total_size = sum(p.stat().st_size for p in _all_mp4s)
            st.success(
                f"✓ {len(_all_mp4s)} קבצים על השרת · "
                f"סה\"כ {_total_size / 1024 / 1024:.1f} MB"
            )
            st.info(
                "💡 **שימו לב:** ההורדה הישירה של Streamlit נתקעת לפעמים לקבצים גדולים. "
                "במקום זה, לחץ '📤 צור לינק קבוע' ליד כל וידאו — הוא יועלה לקטבוקס "
                "(קישור ציבורי, יציב, יש לו CDN משלו), ותקבל לינק שתוכל לפתוח בכרטיסייה חדשה "
                "ולהוריד ישירות מהדפדפן בלי בעיות."
            )

            # Cache uploaded URLs per file in session_state
            _url_cache = st.session_state.setdefault("_video_share_urls", {})

            # ── Bulk upload all → returns a list of shareable links ──
            if st.button(
                f"\U0001F4E4 צור לינקי הורדה לכל ה-{len(_all_mp4s)} הוידאו",
                type="primary",
                use_container_width=True,
                key="upload_all_btn",
                help="מעלה כל וידאו לקטבוקס (קישור קבוע). ייקח כמה שניות לוידאו.",
            ):
                _prog = st.progress(0.0, text="מעלה...")
                for _i, _p in enumerate(_all_mp4s):
                    if str(_p) not in _url_cache:
                        try:
                            _url_cache[str(_p)] = upload_video(_p)
                        except Exception as _e:
                            st.warning(f"\u274C {_p.name}: {_e}")
                    _prog.progress((_i + 1) / len(_all_mp4s), text=f"מעלה {_i+1}/{len(_all_mp4s)}: {_p.name}")
                _prog.empty()
                st.success(f"\u2713 הועלו {len(_url_cache)} וידאו. הקישורים מופיעים למטה.")
                st.rerun()

            st.markdown("---")
            st.markdown(f"**\U0001F4CB רשימת קבצים** (חדשים \u2192 ישנים):")

            # Per-file row: name, mtime, size, action button
            for _p in _all_mp4s:
                _mtime = _dt.fromtimestamp(_p.stat().st_mtime)
                _size_mb = _p.stat().st_size / 1024 / 1024
                _cols = st.columns([3, 2, 1, 2])
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
                            "\u2B07\ufe0f הורד מקטבוקס",
                            _url_cache[_key],
                            use_container_width=True,
                            help="לחץ ימני \u2192 'Save link as...' או פתח בכרטיסייה חדשה",
                        )
                    else:
                        if st.button(
                            "\U0001F4E4 צור לינק קבוע",
                            key=f"upload_one_{_p.name}",
                            use_container_width=True,
                            help="מעלה לקטבוקס, יוצר קישור הורדה ישיר",
                        ):
                            with st.spinner(f"מעלה {_p.name}..."):
                                try:
                                    _url_cache[_key] = upload_video(_p)
                                    st.rerun()
                                except Exception as _e:
                                    st.error(f"שגיאה בהעלאה: {_e}")
