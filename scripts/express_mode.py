"""
Express Mode — minimal UI for: paste prompts → generate videos.

KEY FIX (2026-05-24):
  Stage 4 reads from st.session_state["stage3"], which can be polluted by
  earlier Full-pipeline runs (e.g. 16 plan rows). When the user picks Express,
  we now AUTO-WIPE any non-Express stage3 so Stage 4 only sees fresh Express
  prompts. We also auto-save prompts on every rerun so the user doesn't have
  to click "Save" before scrolling to Stage 4.

Used by app.py via:
    from express_mode import maybe_render_express
    IS_EXPRESS = maybe_render_express(PROJECT_ROOT)

Express mode populates st.session_state["stage3"] (the same key Stage 4 reads
from), so the existing Stage 4 logic generates videos for the manually-pasted
prompts with zero changes to Stage 4 itself.
"""

from pathlib import Path
import streamlit as st


def build_product_asset_sheet_prompt(label: str = "", wear_mode: str = "ring") -> str:
    """Seedream 5.0 / Nano Banana prompt: one reference sheet showing the SAME
    product variant from all sides. Upload the result back as that variant's
    @Image — one sheet gives Seedance every angle it needs.
    """
    desc = label if (label and label.isascii()) else "the product from the attached reference photo"
    use_panel = ("worn on a hand — natural close-up of a hand wearing it"
                 if wear_mode == "ring"
                 else "in use — a hand holding it naturally, close-up")
    return f"""Product reference sheet layout, ONE single image divided into 6 clean panels on a seamless white studio background:
[1] {desc}, facing the camera straight on, centered
[2] left side profile at 90 degrees
[3] right side profile at 90 degrees
[4] top-down view from directly above
[5] extreme macro close-up of the surface texture, edge and any engraving
[6] {use_panel}

EXACTLY the same product in all 6 panels — same color, same material, same proportions, identical details in every panel. The product must match the attached reference photo exactly. Soft even studio lighting, subtle contact shadows, photorealistic commercial product photography, 4K, high detail."""


def build_multi_product_ugc_prompt(n_images: int, roles: list, duration: int,
                                     wear_mode: str = "ring",
                                     size_desc: str = "") -> str:
    """Build a paste-ready Seedance 2.0 UGC prompt that shows ALL uploaded
    product images (@Image 1..N) in one video. Pure string building — no API.
    """
    duration = max(10, min(int(duration), 60))
    labels = []
    for i in range(n_images):
        role = (roles[i].strip() if roles and i < len(roles) and roles[i] else "")
        # Only embed the hint if it's English — Hebrew inside the prompt confuses Seedance
        labels.append(role if role and role.isascii() else "")

    # Time budget: 2s hook, ~2s closing, rest split across products
    body_time = duration - 4
    per = max(2, body_time // max(1, n_images))
    beats = []
    t = 2
    for i in range(n_images):
        ts = f"[00:{t:02d}]"
        what = f" ({labels[i]})" if labels[i] else ""
        if wear_mode == "ring":
            if i == 0:
                beats.append(
                    f"{ts} Jump cut — she slides the ring from @Image 1{what} onto her LEFT index finger, "
                    f"holds her hand up close to the camera and says: \"this is the first one — look at that color.\""
                )
            else:
                beats.append(
                    f"{ts} Jump cut, slightly closer or from a different angle — she swaps to the ring from "
                    f"@Image {i+1}{what} on the SAME LEFT index finger, shows it to the camera and reacts naturally "
                    f"(\"okay this one might be my favorite\" / \"this color goes with everything\" — vary the line)."
                )
        else:
            if i == 0:
                beats.append(
                    f"{ts} Jump cut — she picks up the product from @Image 1{what} in her LEFT hand, "
                    f"holds it close to the camera and says: \"this is the first one — look at this.\""
                )
            else:
                beats.append(
                    f"{ts} Jump cut, slightly closer or from a different angle — she puts the previous one down "
                    f"off-screen and holds up the product from @Image {i+1}{what} in her LEFT hand, reacting naturally "
                    f"(\"okay this one might be my favorite\" — vary the line)."
                )
        t += per
    beats_text = "\n".join(beats)
    img_range = f"@Image 1 through @Image {n_images}"
    if wear_mode == "ring":
        anchor_rule = ("Her LEFT index finger is the only finger that ever wears a ring; "
                       "her right hand stays empty or holds the box.")
        final_line = "she spreads her fingers toward the camera showing the last ring"
        neg_extra = "no duplicate rings, no ring on any other finger"
        scale_line = ("SCALE / TRUE SIZE: each item is a slim silicone ring — a small band "
                      "roughly 2 centimeters (0.8 inch) across that fits on a finger. Keep "
                      "realistic real-world proportions relative to her hand in EVERY frame; "
                      "the ring must never appear larger than her finger, never the size of "
                      "a bracelet or an object held with two hands.")
    else:
        anchor_rule = ("She always holds the product in her LEFT hand; her right hand stays "
                       "empty or gestures only.")
        final_line = "she holds the last product up next to her smile"
        neg_extra = "no duplicate products, nothing held in her right hand"
        size_txt = size_desc.strip() if (size_desc and size_desc.isascii()) else ""
        scale_line = ("SCALE / TRUE SIZE: "
                      + (f"the product's real physical size is: {size_txt}. " if size_txt else "")
                      + "Keep realistic real-world proportions relative to her hands and the "
                      "room in every frame — the product must never be rendered oversized.")

    return f"""{duration}s UGC style product review video, filmed on smartphone, natural window light, front-facing selfie angle. A woman in her late 20s with shoulder-length dark hair, natural human skin (not airbrushed, not plastic), soft matte complexion, wearing a casual oversized t-shirt, sits in a bright lived-in living room — couch with throw pillows, a green plant, a coffee mug on the table behind her.

[00:00] She looks at the camera holding a small open box and says: \"okay so I got the WHOLE color set — let me show you every single one.\"
{beats_text}
[00:{duration-2:02d}] Final shot — {final_line}, smiles and says: \"honestly? get more than one.\"

{scale_line}

PRODUCT CONSISTENCY: every item shown must look IDENTICAL to its source reference — {img_range} must remain visually unchanged across all cuts: same color, same material, same shape as in their respective source images. Each image is ONE separate variant — never merge them, never show a multi-pack as one object. Only ONE item is visible at any moment; the previous one is fully removed off-screen before the next appears. {anchor_rule}

Each jump cut is slightly closer or at a different angle, as if filmed in multiple takes. She speaks casual American English with natural pauses between thoughts. The lighting is natural window light — slightly uneven. The image is natural phone quality, not color graded, soft focus. The sound is direct from the phone mic with faint room ambience.

Negative: {neg_extra}, no on-screen text, no captions or subtitles of any kind, no second person, no brand text overlays, no studio lighting, no cinematic grading."""


try:
    from upload_video import upload_video as _upload_video_to_catbox
except Exception:
    _upload_video_to_catbox = None


EXPRESS_MARKER = "Express campaign"


def _wipe_non_express_stage_state():
    """If stage2/stage3 hold non-Express data (e.g. a 16-row Full plan),
    drop them so Stage 4 doesn't see stale prompts. Idempotent.
    """
    for k in ("stage2", "stage3"):
        v = st.session_state.get(k)
        if isinstance(v, dict) and v.get("campaign_name") != EXPRESS_MARKER:
            st.session_state.pop(k, None)
    # Also drop per-video checkbox state — fresh start.
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith("sel_"):
            st.session_state.pop(key, None)


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
    Returns True if Express mode is active.
    """
    is_express = render_mode_selector()

    # Detect mode transition — when switching INTO Express, wipe stale state.
    prev_mode = st.session_state.get("_last_mode")
    cur_mode = "express" if is_express else "full"
    if prev_mode != cur_mode:
        if is_express:
            _wipe_non_express_stage_state()
        st.session_state["_last_mode"] = cur_mode

    if is_express:
        # Always sanitize before rendering — even on repeat renders, if a
        # full-pipeline action snuck in a non-Express plan we drop it.
        _wipe_non_express_stage_state()
        render_express_ui(project_root)
    return is_express


def _save_express_plan(valid_prompts, gen_audio):
    """Build the campaign dict and write it to session_state. Called both by
    the explicit Save button AND automatically on every rerun (auto-save).
    """
    videos = []
    for idx, p in enumerate(valid_prompts, 1):
        videos.append({
            "id": idx,
            "format": 1,
            "family": "Express",
            "format_name": "Express prompt",
            "duration_seconds": int(p["duration"]),
            "aspect_ratio": p.get("aspect_ratio", "9:16"),
            "generate_audio": bool(gen_audio),
            "prompt": p["prompt"].strip(),
        })
    new_plan = {
        "campaign_name": EXPRESS_MARKER,
        "total_videos": len(videos),
        "videos": videos,
    }
    st.session_state["stage3"] = new_plan
    st.session_state["stage2"] = new_plan  # gates Stage 4
    return new_plan


def render_express_ui(project_root: Path) -> None:
    """Render the Express UI. Populates st.session_state['stage3'] live."""
    st.header("⚡ Express — פרומטים → וידאו")
    st.caption(
        "כתוב את הפרומטים ישירות (משלך / מ-Claude / מ-ChatGPT). "
        "אופציונלי: העלה תמונות מוצר. לחץ ייצור — וזהו."
    )

    # Big visible "Reset" button — clears all Express state so the user can
    # start over without confusion.
    reset_col, info_col = st.columns([1, 3])
    with reset_col:
        if st.button("🧹 איפוס מלא", key="ex_reset_btn",
                      help="מוחק את כל הפרומטים שכתבת ומאפס את שלב 4"):
            for k in list(st.session_state.keys()):
                if isinstance(k, str) and (
                    k.startswith("ex_prompt_")
                    or k.startswith("ex_dur_")
                    or k.startswith("ex_ratio_")
                    or k.startswith("sel_")
                    or k in ("stage2", "stage3", "stage4", "video_results",
                             "split_variant_paths", "split_variant_roles")
                ):
                    st.session_state.pop(k, None)
            st.rerun()
    with info_col:
        st.caption("💡 'איפוס מלא' מנקה הכל ומתחיל מאפס. שימושי אם נראה לך שיש פרומטים ישנים תקועים.")

    col_n, col_d, col_r = st.columns([1, 1, 1])
    with col_n:
        ex_n = st.number_input(
            "כמה וידאו ליצור?",
            min_value=1, max_value=50, value=1, step=1, key="ex_n",
        )
    with col_d:
        ex_default_dur = st.selectbox(
            "משך ברירת מחדל (שניות)",
            [5, 8, 10, 15, 20, 25, 30, 40, 45, 60], index=3,
            format_func=lambda x: f"{x}s" + (f" (×{(x + 14) // 15} chunks)" if x > 15 else ""),
            key="ex_dur",
        )
    with col_r:
        ex_default_ratio = st.selectbox(
            "יחס מסך ברירת מחדל",
            ["adaptive", "9:16", "16:9", "1:1", "4:3", "3:4", "21:9"],
            index=1,
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

        # ── If variants were already auto-split, use them instead of the group photo ──
        _split_paths = st.session_state.get("split_variant_paths")
        if _split_paths and len(ex_image_paths) == 1 and all(Path(sp_).exists() for sp_ in _split_paths):
            ex_image_paths = list(_split_paths)
            st.session_state["image_paths"] = ex_image_paths
            st.session_state["image_path"] = ex_image_paths[0]
            for _i, _r in enumerate(st.session_state.get("split_variant_roles", [])):
                st.session_state.setdefault(f"ex_img_role_{_i}", _r)
            st.info(
                f"✂️ משתמש ב-**{len(ex_image_paths)} הווריאציות שהופרדו אוטומטית** במקום בתמונה המקורית. "
                "רוצה להתחיל מחדש? לחץ '🧹 איפוס מלא' למעלה."
            )

        # ── Auto variant splitter: one group photo → separate variants ──
        if len(ex_image_paths) == 1:
            with st.expander("✂️ יש בתמונה כמה צבעים ביחד? הפרד אוטומטית לתמונות נפרדות", expanded=True):
                st.caption(
                    "אם התמונה מציגה כמה וריאציות של המוצר ביחד (למשל ערימת טבעות ב-7 צבעים) — "
                    "לחיצה אחת: Gemini מזהה כל צבע, יוצר לכל אחד תמונת מוצר נקייה על רקע לבן, "
                    "ונותן שמות אוטומטית. בסוף תקבל @Image נפרד לכל צבע + המחולל ייפתח לבד."
                )
                try:
                    from nano_banana import is_available as _nb_ok
                    _nb_available = _nb_ok()
                except Exception:
                    _nb_available = False
                if not _nb_available:
                    st.warning("חסר GEMINI_API_KEY ב-Secrets — נדרש להפרדה האוטומטית.")
                elif st.button("✂️ הפרד אוטומטית לווריאציות", type="primary",
                                use_container_width=True, key="ex_split_btn"):
                    import importlib as _il
                    import variant_splitter as _vs
                    _il.reload(_vs)
                    with st.status("✂️ מפריד וריאציות...", expanded=True) as _sp:
                        try:
                            _names = _vs.detect_variants(ex_image_paths[0], log=_sp.write)
                            if len(_names) < 2:
                                _sp.update(label="זוהתה וריאציה אחת בלבד — אין מה להפריד", state="complete")
                            else:
                                _sp.write(f"✓ זוהו {len(_names)} וריאציות: " + ", ".join(_names))
                                _results = _vs.extract_variants(
                                    ex_image_paths[0], _names,
                                    save_dir / "variants", log=_sp.write,
                                )
                                st.session_state["split_variant_paths"] = [r_[0] for r_ in _results]
                                st.session_state["split_variant_roles"] = [r_[1] for r_ in _results]
                                _sp.update(label=f"✅ נוצרו {len(_results)} תמונות נפרדות עם שמות", state="complete")
                                st.rerun()
                        except Exception as _e:
                            _sp.update(label=f"❌ {_e}", state="error", expanded=True)

        thumb_cols = st.columns(min(len(ex_image_paths), 5))
        for idx, ip in enumerate(ex_image_paths):
            with thumb_cols[idx % 5]:
                st.image(ip, width=120, caption=f"Image {idx+1}")

        # Per-image role tags + @Image cheat sheet for multi-product videos
        if len(ex_image_paths) > 1:
            st.caption(
                "🏷 **תפקיד לכל תמונה (מומלץ)** — עוזר לך לכתוב פרומט שמשלב "
                "כמה מוצרים/רכיבים בסרטון אחד בלי בלבול."
            )
            ex_roles = []
            role_cols = st.columns(min(len(ex_image_paths), 3))
            for idx in range(len(ex_image_paths)):
                with role_cols[idx % 3]:
                    r = st.text_input(
                        f"@Image {idx+1}",
                        key=f"ex_img_role_{idx}",
                        placeholder="למשל: בקבוק - חזית / רכיב / אריזה",
                    )
                    ex_roles.append(r.strip())
            st.session_state["image_roles"] = ex_roles
            tagged = [f"@Image {i+1} = {r}" for i, r in enumerate(ex_roles) if r]
            if tagged:
                st.info(
                    "📋 **מפת רפרנסים לפרומט** — העתק לפרומט ועגן כל beat לתמונה הנכונה:\n\n"
                    + "\n".join(f"- `{t}`" for t in tagged)
                    + "\n\nדוגמה: *\"[00:00] she holds @Image 1 ... [00:05] close-up on @Image 2 next to it — "
                    "all references must remain visually unchanged across cuts.\"*"
                )
        else:
            st.session_state["image_roles"] = []

        # ── Auto prompt generator: one UGC video that shows ALL products ──
        if len(ex_image_paths) > 1:
            with st.expander("🪄 מחולל אוטומטי: פרומט UGC אחד שמציג את כל המוצרים", expanded=True):
                st.caption(
                    f"העלית {len(ex_image_paths)} תמונות — לחיצה אחת בונה פרומט מוכן שבו הדמות "
                    "מדברת על כל הווריאציות ומראה כל אחת מהן, אחת אחרי השנייה, עם כל חוקי העקביות."
                )
                gen_mode = st.radio(
                    "איך מציגים כל מוצר?",
                    ["💍 נלבש על אצבע (טבעות)", "🤲 מוחזק ביד (כל מוצר אחר)"],
                    index=0, horizontal=True, key="ex_gen_mode",
                )
                gen_size = ""
                if gen_mode.startswith("🤲"):
                    gen_size = st.text_input(
                        "גודל אמיתי של המוצר (באנגלית — חשוב לפרופורציות!)",
                        key="ex_gen_size",
                        placeholder="e.g. a 25cm tall bottle / a palm-sized jar / a 10cm box",
                    )
                gen_dur = st.select_slider(
                    "משך הסרטון לפרומט",
                    options=[10, 15, 20, 25, 30],
                    value=15 if len(ex_image_paths) <= 5 else 20,
                    key="ex_gen_dur",
                    help="מעל 15 שניות = הסרטון ייווצר בכמה חלקים שיודבקו אוטומטית.",
                )
                gen_prompt = build_multi_product_ugc_prompt(
                    len(ex_image_paths),
                    st.session_state.get("image_roles", []),
                    int(gen_dur),
                    wear_mode="ring" if gen_mode.startswith("💍") else "held",
                    size_desc=gen_size,
                )
                if st.button("🪄 בנה פרומט לכל המוצרים → וידאו #1", type="primary",
                              use_container_width=True, key="ex_gen_btn"):
                    st.session_state["ex_prompt_0"] = gen_prompt
                    st.session_state["ex_dur_0"] = int(gen_dur)
                    st.success("✅ הפרומט נכנס לוידאו #1 למטה — אפשר לערוך אותו ואז לגלול לשלב 4 לייצור.")
                with st.expander("👁 תצוגה מקדימה של הפרומט", expanded=False):
                    st.code(gen_prompt, language=None)

            # ── Multi-angle reference sheets: one image per variant, all sides ──
            with st.expander("🖼 מחולל תמונות מכל הזוויות (Reference Sheet לכל צבע)", expanded=False):
                st.caption(
                    "לכל וריאציה נבנה פרומט ל-**Seedream 5.0 / Nano Banana**: תמונה אחת עם 6 פאנלים — "
                    "חזית, שני פרופילים, מלמעלה, מאקרו, ועל היד. מדביקים את הפרומט במחולל התמונות "
                    "**עם התמונה המקורית מצורפת**, ואת התוצאה מעלים לכאן בחזרה במקום התמונה המקורית — "
                    "ככה סידנס מקבלת את כל הזוויות של כל טבעת בתמונה אחת ויכולה להנפיש אותה מכל כיוון."
                )
                sheet_mode = "ring" if st.session_state.get("ex_gen_mode", "💍").startswith("💍") else "held"
                roles_now = st.session_state.get("image_roles", [])
                for idx in range(len(ex_image_paths)):
                    label = roles_now[idx] if idx < len(roles_now) else ""
                    title = label if label else f"Image {idx+1}"
                    st.markdown(f"**@Image {idx+1} — {title}**")
                    st.code(build_product_asset_sheet_prompt(label, sheet_mode), language=None)

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
    st.checkbox(
        "🫥 טשטש פנים אוטומטית בוידאו רפרנס (עוקף את המסנן של Seedance)",
        value=True,
        key="ex_blur_faces",
        help=(
            "Seedance חוסמת וידאו רפרנס שיש בו פנים אמיתיים. "
            "האפשרות הזאת מטשטשת פנים אוטומטית לפני העלאה — Seedance עדיין לומדת "
            "את הסגנון, התנועה והקומפוזיציה (זה כל מה שהיא משתמשת מהרפרנס), "
            "ופנים אמיתיים נחסכים מהסינון. כבה אם הוידאו כבר נקי מאנשים."
        ),
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
                    min_value=5, max_value=60, value=int(ex_default_dur), step=1,
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

    # AUTO-SAVE — every rerun, push the latest prompts into stage3.
    # The user doesn't have to click "Save" — what they see in the boxes is
    # what Stage 4 will generate. We always REPLACE any older data.
    if valid:
        _save_express_plan(valid, ex_gen_audio)
        st.success(
            f"\u2705 {len(valid)} פרומטים פעילים מתוך {int(ex_n)}. "
            f"גלול ל-'5\ufe0f\u20e3 שלב 4' לייצור."
        )
    else:
        # No valid prompts — wipe Express plan so Stage 4 stays disabled.
        st.session_state.pop("stage3", None)
        st.session_state.pop("stage2", None)
        st.info(f"\U0001F4A1 כתוב פרומט באחד מ-{int(ex_n)} השדות למעלה.")

    st.markdown("---")
    st.caption("\u2B07 גלול מטה ל-'5\ufe0f\u20e3 שלב 4' לייצור הוידאו.")
    st.markdown("---")
