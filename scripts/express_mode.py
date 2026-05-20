"""
Express Mode — minimal UI for: paste prompts → generate videos.

Used by app.py via:
    from express_mode import render_express_ui, is_express_selected
    is_express = render_mode_selector()
    if is_express:
        render_express_ui(PROJECT_ROOT)
    # Stage 4 below still renders, reads st.session_state["stage3"]

Express mode populates st.session_state["stage3"] (the same key Stage 4 reads
from), so the existing Stage 4 logic generates videos for the manually-pasted
prompts with zero changes to Stage 4 itself.
"""

from pathlib import Path
import streamlit as st

try:
    from upload_video import upload_video as _upload_video_to_catbox
except Exception:
    _upload_video_to_catbox = None


def render_mode_selector() -> bool:
    """Returns True if the user picked Express mode."""
    mode = st.radio(
        "מצב עבודה",
        ["⚡ Express — פרומטים מוכנים → ייצור וידאו (קצר ופשוט)",
         "🔬 Full pipeline — מחקר, תכנון, פרומטים, וידאו (המסלול המלא)"],
        index=0,
        horizontal=True,
        key="mode_selector",
    )
    return mode.startswith("⚡")


def maybe_render_express(project_root) -> bool:
    """Single entry point — renders mode selector and Express UI if chosen.
    Returns True if Express mode is active (caller can use this to skip
    the Full pipeline UI). Caller only needs:
        is_express = express_mode.maybe_render_express(PROJECT_ROOT)
    """
    is_express = render_mode_selector()
    if is_express:
        render_express_ui(project_root)
    return is_express


def render_express_ui(project_root: Path) -> None:
    """Render the Express UI. Sets st.session_state['stage3'] when user saves."""
    st.header("⚡ Express — פרומטים → וידאו")
    st.caption(
        "כתוב את הפרומטים ישירות (משלך / מ-Claude / מ-ChatGPT). "
        "אופציונלי: העלה תמונות מוצר. לחץ ייצור — וזהו."
    )

    col_n, col_d, col_r = st.columns([1, 1, 1])
    with col_n:
        ex_n = st.number_input(
            "כמה וידאו ליצור?",
            min_value=1, max_value=50, value=3, step=1, key="ex_n",
        )
    with col_d:
        ex_default_dur = st.selectbox(
            "משך ברירת מחדל (שניות)",
            [5, 8, 10, 15, 20, 25, 30], index=3,
            format_func=lambda x: f"{x}s" + (" (×2 chunks)" if x > 15 else ""),
            key="ex_dur",
        )
    with col_r:
        ex_default_ratio = st.selectbox(
            "יחס מסך ברירת מחדל",
            ["adaptive", "9:16", "16:9", "1:1", "4:3", "3:4", "21:9"],
            index=1,  # 9:16 default (TikTok/Reels)
            format_func=lambda x: {
                "adaptive": "🤖 אוטומטי (לפי הרפרנס)",
                "9:16": "📱 9:16 — אנכי (TikTok/Reels)",
                "16:9": "🖥 16:9 — אופקי (YouTube/CTV)",
                "1:1": "⏹ 1:1 — מרובע (Instagram feed)",
                "4:3": "📺 4:3 — קלאסי",
                "3:4": "📐 3:4 — דיוקן קלאסי",
                "21:9": "🎬 21:9 — קולנועי",
            }[x],
            key="ex_ratio",
        )

    ex_gen_audio = st.checkbox(
        "🔊 ייצור אודיו (Seedance מוסיף קול/דיאלוג)",
        value=True,
        key="ex_gen_audio",
        help=(
            "כבה אם Seedance מסרב ליצור את הוידאו עם השגיאה "
            "'OutputAudioSensitiveContentDetected'. הוידאו ייווצר ללא אודיו."
        ),
    )

    st.markdown("**🖼 תמונות מוצר (אופציונלי — עד 9)**")
    ex_uploaded = st.file_uploader(
        "אם הפרומט מזכיר Image 1 / Image 2 — חובה להעלות. אחרת אופציונלי.",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="ex_uploader",
    )
    if ex_uploaded:
        save_dir = project_root / "assets" / "product"
        save_dir.mkdir(parents=True, exist_ok=True)
        ex_image_paths = []
        for uf in ex_uploaded[:9]:
            path = save_dir / uf.name
            path.write_bytes(uf.getvalue())
            ex_image_paths.append(str(path))
        st.session_state["image_paths"] = ex_image_paths
        st.session_state["image_path"] = ex_image_paths[0]
        thumb_cols = st.columns(min(len(ex_image_paths), 5))
        for idx, ip in enumerate(ex_image_paths):
            with thumb_cols[idx % 5]:
                st.image(ip, width=120, caption=f"Image {idx+1}")

    # Reference videos — Seedance imitates style/motion from these
    st.markdown("**🎥 וידאו רפרנס (אופציונלי — עד 3, כל אחד ≤15 שניות)**")
    st.caption(
        "אם יש לך וידאו דוגמה (קליפ של מתחרה / יוצר אחר / וידאו ישן שלכם) — "
        "העלה אותו כאן, וקלוד ינסה לעשות חיקוי בסגנון/בתנועה, רק עם המוצר שלך והדמות שלך."
    )
    ex_video_refs = st.file_uploader(
        "MP4 בלבד, עד 3 קבצים",
        type=["mp4", "mov", "webm"],
        accept_multiple_files=True,
        key="ex_video_refs",
    )
    if ex_video_refs:
        ref_dir = project_root / "assets" / "ref_videos"
        ref_dir.mkdir(parents=True, exist_ok=True)
        ref_paths = []
        for vf in ex_video_refs[:3]:
            p = ref_dir / vf.name
            p.write_bytes(vf.getvalue())
            ref_paths.append(str(p))
        st.session_state["ref_video_paths"] = ref_paths
        st.success(f"✓ {len(ref_paths)} וידאו רפרנס מוכנים. יועלו לקטבוקס בזמן ייצור.")
    else:
        st.session_state.pop("ref_video_paths", None)

    st.markdown(f"**📝 כתוב {int(ex_n)} פרומטים** (כל אחד נפרד):")
    ex_prompts = []
    for i in range(int(ex_n)):
        with st.expander(f"וידאו #{i+1}", expanded=(i == 0)):
            txt = st.text_area(
                f"פרומט וידאו {i+1}",
                height=180,
                key=f"ex_prompt_{i}",
                placeholder=(
                    "Example: A 30-year-old woman in a sunlit kitchen, "
                    "holding Image 1, saying 'okay so I tried this for a week and...'. "
                    "Phone-quality footage, casual UGC vibe, 3-4 jump cuts, English audio."
                ),
                label_visibility="collapsed",
            )
            dc, rc = st.columns([1, 1])
            with dc:
                dur_i = st.number_input(
                    f"משך וידאו {i+1} (שניות)",
                    min_value=5, max_value=30, value=int(ex_default_dur), step=1,
                    key=f"ex_dur_{i}",
                )
            with rc:
                ratio_options = ["(ברירת מחדל)", "adaptive", "9:16", "16:9", "1:1", "4:3", "3:4", "21:9"]
                ratio_i = st.selectbox(
                    f"יחס מסך וידאו {i+1}",
                    ratio_options,
                    index=0,
                    key=f"ex_ratio_{i}",
                    help="(ברירת מחדל) משתמש ביחס שבחרת למעלה",
                )
            actual_ratio = ex_default_ratio if ratio_i == "(ברירת מחדל)" else ratio_i
            ex_prompts.append({
                "prompt": txt,
                "duration": dur_i,
                "aspect_ratio": actual_ratio,
            })

    valid = [p for p in ex_prompts if p["prompt"].strip()]
    save_col, info_col = st.columns([1, 2])
    with save_col:
        clicked = st.button(
            f"💾 שמור {len(valid)} פרומטים והמשך לייצור",
            type="primary",
            disabled=len(valid) == 0,
            use_container_width=True,
            key="ex_save_btn",
        )
        if clicked:
            videos = []
            for idx, p in enumerate(valid, 1):
                videos.append({
                    "id": idx, "format": 1, "family": "Express",
                    "format_name": "Express prompt",
                    "duration_seconds": int(p["duration"]),
                    "aspect_ratio": p.get("aspect_ratio", "9:16"),
                    "generate_audio": bool(ex_gen_audio),
                    "prompt": p["prompt"].strip(),
                })
            new_plan = {
                "campaign_name": "Express campaign",
                "total_videos": len(videos),
                "videos": videos,
            }
            st.session_state["stage3"] = new_plan
            st.session_state["stage2"] = new_plan  # gates Stage 4
            st.success(
                f"✓ {len(valid)} פרומטים מוכנים. גלול ל-'5️⃣ שלב 4' לייצור."
            )
    with info_col:
        if len(valid) == 0:
            st.info("💡 כתוב לפחות פרומט אחד.")
        else:
            st.info(
                f"💡 מוכנים {len(valid)} פרומטים — לחץ 'שמור' כדי לאפשר את שלב 4."
            )

    st.markdown("---")
    st.caption("⬇ גלול מטה ל-'5️⃣ שלב 4' לייצור הוידאו.")
    st.markdown("---")
