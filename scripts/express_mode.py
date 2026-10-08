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
                                     size_desc: str = "",
                                     sheets_active: bool = False) -> str:
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
        neg_extra = ("no duplicate rings, no ring on any other finger, "
                     "no warped or deformed ring geometry")
        scale_line = ("SCALE / TRUE SIZE: each item is a slim silicone ring — a small band "
                      "roughly 2 centimeters (0.8 inch) across that fits on a finger. Keep "
                      "realistic real-world proportions relative to her hand in EVERY frame; "
                      "the ring must never appear larger than her finger, never the size of "
                      "a bracelet or an object held with two hands. GEOMETRY: the ring is a "
                      "perfectly smooth, evenly-thick circular band — its shape must stay "
                      "perfect in every frame: no warping, no bending, no melting, no "
                      "squashing, no oval distortion.")
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

    sheets_block = ("\nREFERENCE SHEETS: each @Image is a multi-angle reference sheet of ONE "
                    "variant (front, side profiles, top-down, macro texture, worn on hand). "
                    "The item in the video must match its sheet exactly — same shape, same "
                    "thickness, same proportions, from every camera angle.\n"
                    if sheets_active else "")

    return f"""{duration}s UGC style product review video, filmed on smartphone, natural window light, front-facing selfie angle. A woman in her late 20s with shoulder-length dark hair, natural human skin (not airbrushed, not plastic), soft matte complexion, wearing a casual oversized t-shirt, sits in a bright lived-in living room — couch with throw pillows, a green plant, a coffee mug on the table behind her.

[00:00] She looks at the camera holding a small open box and says: \"okay so I got the WHOLE color set — let me show you every single one.\"
{beats_text}
[00:{duration-2:02d}] Final shot — {final_line}, smiles and says: \"honestly? get more than one.\"

{scale_line}
{sheets_block}
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


SHOW_FULL_PIPELINE = False


def render_mode_selector() -> bool:
    """Returns True if the user picked Express mode.

    Full pipeline is hidden for now (not in use). Set SHOW_FULL_PIPELINE = True
    to bring the selector back.
    """
    if not SHOW_FULL_PIPELINE:
        return True
    mode = st.radio(
        "Work mode",
        ["⚡ Express — ready-made prompts → video generation (quick and simple)",
         "🔬 Full pipeline — research, planning, prompts, video (the full route)"],
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


NO_MUSIC_RULE = ("Audio: no background music and no songs — only natural ambient sound "
                 "and the character's own voice if they speak.")


def _with_audio_rule(prompt, gen_audio):
    """Append the no-music rule when audio is on and the user opted in."""
    if gen_audio and st.session_state.get("ex_no_music", True) and NO_MUSIC_RULE not in prompt:
        return prompt.rstrip() + "\n\n" + NO_MUSIC_RULE
    return prompt


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
            "resolution": st.session_state.get("ex_res", "720p"),
            "engine": "2.5" if st.session_state.get("ex_engine", "").startswith("🚀") else "2.0",
            "prompt": _with_audio_rule(p["prompt"].strip(), gen_audio),
        })
    new_plan = {
        "campaign_name": EXPRESS_MARKER,
        "total_videos": len(videos),
        "videos": videos,
    }
    st.session_state["stage3"] = new_plan
    st.session_state["stage2"] = new_plan  # gates Stage 4
    return new_plan


def _render_character_library(project_root: Path) -> list:
    """C) Upload our AI characters to the ModelArk Virtual Portrait library and
    pick verified characters (AI + Real-human) for the video. Returns the list
    of selected asset:// references."""
    import importlib as _ill
    import asset_library as _al
    _ill.reload(_al)

    st.markdown("**C) My character library (upload once, reuse in every video)**")
    if not _al.is_configured():
        st.info(
            "To upload AI characters straight from here, add two keys to **Streamlit → Settings → "
            "Secrets**:\n\n```\nBYTEPLUS_ACCESS_KEY = \"AKLT...\"\nBYTEPLUS_SECRET_KEY = \"...\"\n```\n"
            "Create them in the BytePlus console → your name (top right) → **API Access Keys**. "
            "(These are different from the ARK API key.) Until then you can still paste Asset IDs above."
        )
        return []

    # ---- Upload a new AI character ----
    with st.container(border=True):
        st.markdown("➕ **Add an AI character** (must not resemble a real person)")
        _cname = st.text_input("Character name", key="lib_new_name",
                               placeholder="e.g. Young man black jacket")
        _cfiles = st.file_uploader(
            "Images of THIS character (1–4). Best: a front face close-up + a full-body shot, vertical.",
            type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="lib_new_files")
        _go = st.button("⬆️ Upload to my library", type="primary", key="lib_upload_btn",
                        disabled=not (_cname.strip() and _cfiles), use_container_width=True)
        if _go:
            from upload_image import _prepare_for_upload, host_image_bytes
            with st.status(f"Uploading '{_cname.strip()}'…", expanded=True) as _s:
                try:
                    _gid = _al.ensure_group(_cname.strip())
                    _s.write(f"📁 Character group: {_gid}")
                    _ok, _fail = 0, 0
                    for _i, _uf in enumerate(_cfiles[:4], 1):
                        _tmp = Path(project_root) / "assets" / "lib_upload" / _uf.name
                        _tmp.parent.mkdir(parents=True, exist_ok=True)
                        _tmp.write_bytes(_uf.getvalue())
                        _data = _prepare_for_upload(_tmp)
                        _url = host_image_bytes(_data, f"char_{_i}.jpg", log=_s.write)
                        if _i > 1:
                            _s.write("  ⏳ waiting ~20s (free plan: 3 uploads per minute)…")
                        _aid = _al.create_asset(_gid, _url, name=f"{_cname.strip()} {_i}")
                        _s.write(f"  📤 Image {_i} sent → {_aid}, waiting for approval…")
                        _res = _al.wait_active(_aid, log=_s.write)
                        if _res.get("Status") == "Active":
                            _ok += 1
                            _s.write(f"  ✅ Image {_i} approved")
                        else:
                            _fail += 1
                            _s.write(f"  ❌ Image {_i} not approved: "
                                     f"{_res.get('Status') or 'timeout'} {_res.get('ErrorMessage') or ''}")
                    _s.update(label=f"Done — {_ok} approved, {_fail} failed",
                              state="complete" if _ok else "error")
                    st.session_state.pop("_lib_cache", None)
                except Exception as _e:
                    _s.update(label=f"❌ {_e}", state="error", expanded=True)

    # ---- Library list ----
    if st.button("🔄 Refresh library", key="lib_refresh"):
        st.session_state.pop("_lib_cache", None)
    _cache = st.session_state.get("_lib_cache")
    if _cache is None:
        try:
            _cache = {
                "aigc": _al.list_assets("AIGC"),
                "real": _al.list_assets("LivenessFace"),
                "groups": {g["Id"]: g.get("Name", "") for g in _al.list_groups("AIGC")},
            }
            st.session_state["_lib_cache"] = _cache
        except Exception as _e:
            st.error(f"Couldn't load the library: {_e}")
            return []

    _all = [("AI", a) for a in _cache["aigc"]] + [("Real", a) for a in _cache["real"]]
    st.caption(f"{len(_all)} / {_al.FREE_PLAN_LIMIT} assets used (free plan). "
               "Delete characters you no longer need to free space.")
    if not _all:
        st.caption("No approved characters yet.")
        return []

    _sel = st.session_state.setdefault("_lib_selected", {})
    _cols = st.columns(4)
    for _i, (_kind, _a) in enumerate(_all):
        _aid = _a.get("Id", "")
        _label = _a.get("Name") or _cache["groups"].get(_a.get("GroupId"), "") or _aid[-6:]
        with _cols[_i % 4]:
            if _a.get("URL"):
                st.image(_a["URL"], use_container_width=True)
            _sel[_aid] = st.checkbox(f"{'🧑‍🎤' if _kind == 'AI' else '👤'} {_label}",
                                     value=_sel.get(_aid, False), key=f"lib_sel_{_aid}")

    # ---- Delete a whole AI character (frees space) ----
    _gmap = _cache["groups"]
    if _gmap:
        with st.expander("🗑 Delete an AI character (frees space — permanent)", expanded=False):
            _gid_del = st.selectbox("Character", list(_gmap.keys()), key="lib_del_pick",
                                    format_func=lambda g: _gmap.get(g) or g)
            _confirm = st.checkbox("Yes, delete this character and all its images permanently",
                                   key="lib_del_confirm")
            if st.button("Delete", key="lib_del_btn", disabled=not _confirm):
                try:
                    _al.delete_group(_gid_del)
                    st.session_state.pop("_lib_cache", None)
                    st.success("Deleted.")
                    st.rerun()
                except Exception as _e:
                    st.error(str(_e))

    return [f"asset://{aid}" for aid, on in _sel.items() if on]


def _render_official_faces(project_root: Path) -> None:
    """Official ByteDance face support for Seedance 2.0/2.5 — no filter fights.
      A) Trusted AI characters: Seedream 5.0 lite text-to-image on the SAME
         ModelArk account → original URL passes the face check (30-day trust).
      B) Asset IDs from the ModelArk private asset library (Virtual Portrait /
         Real-human) → asset://<id>.
    Results land in st.session_state['trusted_char_urls'] / ['asset_ref_urls'],
    which Stage 4 appends right after the product images."""
    import importlib as _ilf
    import trusted_refs as _tr
    _ilf.reload(_tr)

    n_products = len(st.session_state.get("image_paths") or [])
    with st.expander("🧑‍🎤 Faces & My character library — official ByteDance (click to open)", expanded=False):
        st.caption(
            "Seedance blocks uploaded photos of faces. ByteDance's official ways around it "
            "(no tricks, no blocks): **A)** generate the character on your own ModelArk account "
            "with Seedream 5.0 lite — its original image is trusted; or **B)** use portraits "
            "verified in your ModelArk asset library (paste their Asset IDs)."
        )

        # ── A) Trusted Seedream character ──
        st.markdown("**A) Create a trusted AI character (Seedream 5.0 lite)**")
        _c_prompt = st.text_area(
            "Describe the character (text only — no image upload, that's what makes it trusted)",
            key="seedream_char_prompt", height=90,
            placeholder="Vertical portrait photo of a friendly woman in her late 20s, shoulder-length "
                        "dark hair, light makeup, white t-shirt, bright kitchen background, natural light, "
                        "looking at the camera, upper body",
        )
        _cc1, _cc2 = st.columns([1, 2])
        with _cc1:
            _c_size = st.selectbox("Size", ["2K", "4K"], index=0, key="seedream_char_size")
        with _cc2:
            st.write("")
            _go = st.button("🎨 Generate trusted character", use_container_width=True,
                            key="seedream_char_btn", disabled=not _c_prompt.strip())
        if _go:
            from byteplus_client import seedream_generate
            with st.spinner("Seedream 5.0 lite is creating the character..."):
                try:
                    _url = seedream_generate(_c_prompt.strip(), size=_c_size)
                    _tr.record("image", _url, _c_prompt.strip()[:60])
                    st.session_state.setdefault("_char_selected", {})[_url] = True
                    st.success("✅ Character created — it's selected as a reference below.")
                except Exception as _e:
                    st.error(str(_e))

        _chars = _tr.active("image")
        _sel = st.session_state.setdefault("_char_selected", {})
        if _chars:
            st.caption("Your trusted characters (original URLs stay valid ~24h — generate a new one after that):")
            _cols = st.columns(min(len(_chars), 4))
            for _i, _it in enumerate(_chars[:8]):
                with _cols[_i % 4]:
                    st.image(_it["url"], use_container_width=True)
                    _sel[_it["url"]] = st.checkbox(
                        f"Use · {_tr.age_label(_it)}", value=_sel.get(_it["url"], False),
                        key=f"char_use_{_i}_{abs(hash(_it['url'])) % 10**8}")
        st.session_state["trusted_char_urls"] = [i["url"] for i in _chars if _sel.get(i["url"])]

        st.markdown("---")
        # ── B) Asset library IDs ──
        st.markdown("**B) Portraits from your ModelArk asset library**")
        st.caption(
            "Upload your character in the BytePlus console → ModelArk → Playground → My assets → "
            "**Virtual Portrait** → Manage assets (AI characters) — or **Real-human** for real people, "
            "which needs company verification. When the status is *Verification successful*, copy the "
            "**Asset ID** and paste it here (one per line). Requires 'Advanced Creation Rights' on the account."
        )
        _ids_txt = st.text_area("Asset IDs", key="asset_ids_input", height=70,
                                placeholder="asset-20260909195044-229hs")
        from byteplus_client import normalize_asset_ref
        _assets, _bad = [], []
        for _line in _ids_txt.splitlines():
            if not _line.strip():
                continue
            _ref = normalize_asset_ref(_line)
            (_assets if _ref else _bad).append(_ref or _line.strip())
        if _bad:
            st.warning("Not an Asset ID (should start with 'asset-'): " + ", ".join(_bad))

        st.markdown("---")
        # ── C) My character library (Virtual Portrait + Real-human, via API) ──
        _lib_selected = _render_character_library(project_root)
        for _ref in _lib_selected:
            if _ref not in _assets:
                _assets.append(_ref)
        st.session_state["asset_ref_urls"] = _assets

        # ── Mapping preview: how to refer to them in the prompt ──
        _faces = st.session_state["trusted_char_urls"] + _assets
        if _faces:
            _lines = [f"- Product images → @Image 1–{n_products}" if n_products > 1 else
                      ("- Product image → @Image 1" if n_products == 1 else "- (no product images)")]
            for _k in range(len(_faces)):
                _lines.append(f"- Face reference {_k + 1} → **@Image {n_products + _k + 1}**")
            st.info("**In your prompt, refer to them like this** (never by Asset ID):\n\n" + "\n".join(_lines))


def _render_video_editor(project_root: Path) -> None:
    """Seedance 2.5 V2V — edit or extend an already-generated video."""
    with st.expander("🎞 Edit an existing video (Seedance 2.5) — replace / remove / change, or extend", expanded=False):
        st.caption(
            "Upload a video you already made and describe a change — e.g. "
            "\"replace the gun with a book\", \"remove the logo on the wall\", "
            "\"change the shirt to blue\" — or extend it past its last frame. "
            "Uses Seedance 2.5 (needs 2.5 API access on your ModelArk account)."
        )
        import trusted_refs as _tr_ve
        _recent = _tr_ve.active("video")
        _src_opts = ["⬆️ Upload a video file"]
        if _recent:
            _src_opts.insert(0, "🎬 A video generated here in the last 24h (trusted — faces OK)")
        _src_opts.append("🗂 An Asset ID from my ModelArk asset library")
        _ve_src_mode = st.radio("Source video (@Video 1)", _src_opts, index=0, key="ve_src_mode")
        _ve_file, _ve_source_url = None, None
        if _ve_src_mode.startswith("🎬"):
            _pick = st.selectbox(
                "Pick the video", range(len(_recent)), key="ve_recent_pick",
                format_func=lambda i: f"{_recent[i]['label']} · {_tr_ve.age_label(_recent[i])}")
            _ve_source_url = _recent[_pick]["url"]
            st.video(_ve_source_url)
        elif _ve_src_mode.startswith("🗂"):
            from byteplus_client import normalize_asset_ref
            _aid = st.text_input("Asset ID", key="ve_asset_id", placeholder="asset-2026…")
            _ve_source_url = normalize_asset_ref(_aid)
            if _aid.strip() and not _ve_source_url:
                st.warning("Asset IDs start with 'asset-'.")
        else:
            st.caption("⚠️ Uploaded files with realistic faces are blocked by Seedance — for faces, "
                       "use a video generated here (trusted) or an asset-library ID.")
            _ve_file = st.file_uploader(
                "Source video (MP4/MOV, ≤15s works best)",
                type=["mp4", "mov", "webm"], key="ve_uploader",
            )
        _ve_mode = st.radio(
            "Operation",
            ["✏️ Edit (change something in the video)",
             "➕ Extend (continue past the last frame)"],
            index=0, horizontal=True, key="ve_mode",
        )

        # Reference images (@Image 1..) — e.g. the new jacket / product / background
        st.markdown("**🖼 Reference images (optional) — @Image 1, @Image 2 …**")
        st.caption(
            "Upload what you want to bring INTO the video (a garment, a product, a "
            "background) and point to it in the text — e.g. "
            "*\"change the shirt in @Video 1 to the jacket in @Image 1\"*."
        )
        _ve_imgs = st.file_uploader(
            "Reference images (up to 9)",
            type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
            key="ve_img_uploader",
        )
        if _ve_imgs:
            _vc = st.columns(min(len(_ve_imgs), 5))
            for _i, _uf in enumerate(_ve_imgs[:9]):
                with _vc[_i % 5]:
                    st.image(_uf.getvalue(), width=90, caption=f"@Image {_i+1}")

        # Extra reference videos (@Video 2..) — style/motion source
        st.markdown("**🎥 Extra reference videos (optional) — @Video 2, @Video 3**")
        _ve_extra_vids = st.file_uploader(
            "Extra clips (up to 2) — style / motion reference",
            type=["mp4", "mov", "webm"], accept_multiple_files=True,
            key="ve_extra_vid_uploader",
        )

        _ve_instr = st.text_area(
            "Describe the change" if str(st.session_state.get("ve_mode", "")).startswith("✏️")
            else "Describe what happens next",
            height=90, key="ve_instr",
            placeholder="e.g. Change the shirt in @Video 1 to the jacket in @Image 1. Keep everything else identical.",
        )
        _c1, _c2, _c3 = st.columns(3)
        with _c1:
            _ve_dur = st.number_input("Output seconds", min_value=4, max_value=30,
                                      value=5, step=1, key="ve_dur")
        with _c2:
            _ve_ratio = st.selectbox("Aspect", ["9:16", "16:9", "1:1", "4:3", "3:4"],
                                     index=0, key="ve_ratio")
        with _c3:
            _ve_res = st.selectbox("Quality", ["480p", "720p", "1080p"], index=1, key="ve_res")
        _ve_audio = st.checkbox("🔊 Generate audio", value=True, key="ve_audio")

        _disabled = not ((_ve_file or _ve_source_url) and _ve_instr.strip())
        if st.button("🎬 Generate edited video", type="primary",
                      use_container_width=True, disabled=_disabled, key="ve_go"):
            import importlib as _ilv
            import video_edit as _vev
            _ilv.reload(_vev)
            from datetime import datetime as _dtv
            _src_dir = project_root / "assets" / "edit_src"
            _src_dir.mkdir(parents=True, exist_ok=True)
            if _ve_file is not None:
                _src = _src_dir / _ve_file.name
                _src.write_bytes(_ve_file.getvalue())
            else:
                _src = None
            _ts = _dtv.now().strftime("%Y%m%d_%H%M%S")
            _out = project_root / "outputs" / "videos" / f"edited_{_ts}.mp4"
            # Save reference images / extra videos to disk
            _ve_img_paths = []
            for _uf in (_ve_imgs or [])[:9]:
                _ip = _src_dir / f"ref_{_ts}_{_uf.name}"
                _ip.write_bytes(_uf.getvalue())
                _ve_img_paths.append(str(_ip))
            _ve_vid_paths = []
            for _uf in (_ve_extra_vids or [])[:2]:
                _vp = _src_dir / f"refvid_{_ts}_{_uf.name}"
                _vp.write_bytes(_uf.getvalue())
                _ve_vid_paths.append(str(_vp))
            with st.status("🎞 Editing via Seedance 2.5...", expanded=True) as _vs:
                try:
                    _res = _vev.edit_video(
                        _src, _ve_instr.strip(), _out,
                        source_url=_ve_source_url,
                        image_paths=_ve_img_paths or None,
                        extra_video_paths=_ve_vid_paths or None,
                        ratio=_ve_ratio, duration=int(_ve_dur), resolution=_ve_res,
                        generate_audio=_ve_audio,
                        extend=str(st.session_state.get("ve_mode", "")).startswith("➕"),
                        log=_vs.write,
                    )
                    _vs.update(label="✅ Edited video ready", state="complete")
                    st.video(str(_res))
                    with open(_res, "rb") as _f:
                        st.download_button("⬇️ Download edited video", _f.read(),
                                           file_name=_res.name, mime="video/mp4",
                                           key="ve_dl")
                except Exception as _e:
                    _vs.update(label=f"❌ {_e}", state="error", expanded=True)


def _clear_express(full: bool) -> None:
    """New video (full=False): clear prompts + Stage-4 marks.
    Full reset (full=True): also uploaded images, faces, references.
    The session's video gallery ('video_history') is always kept."""
    ss = st.session_state
    for k in list(ss.keys()):
        if not isinstance(k, str):
            continue
        if (k.startswith("ex_prompt_") or k.startswith("sel_")
                or k in ("stage2", "stage3", "video_results")):
            ss.pop(k, None)
    if full:
        for k in ("image_path", "image_paths", "image_roles", "ref_video_paths",
                  "split_variant_paths", "split_variant_roles", "_autoname_sig",
                  "sheet_variant_paths", "_sheets_src_sig", "_sheets_active",
                  "ai_char_paths", "ai_char_confirmed", "ai_char_originals", "ai_char_prepared",
                  "trusted_char_urls", "asset_ref_urls", "asset_ids_input",
                  "_char_selected", "_lib_selected"):
            ss.pop(k, None)
        for k in list(ss.keys()):
            if isinstance(k, str) and (k.startswith("char_use_") or k.startswith("lib_sel_")
                                          or k.startswith("ex_img_role_")):
                ss.pop(k, None)
        # New uploader keys = empty upload boxes
        ss["_ex_gen"] = int(ss.get("_ex_gen", 0)) + 1


def render_express_ui(project_root: Path) -> None:
    """Render the Express UI. Populates st.session_state['stage3'] live."""
    st.header("⚡ Express — Prompts → Video")
    st.caption(
        "Write your prompts directly (your own / from Claude / from ChatGPT). "
        "Optional: upload product images. Click generate — that's it."
    )

    _render_video_editor(project_root)

    # Two clear restart buttons. Generated videos are NEVER wiped — they stay
    # in "Your generated videos" below for the whole session.
    _r1, _r2, _r3 = st.columns([1, 1, 2])
    with _r1:
        if st.button("🆕 New video", key="ex_new_btn", use_container_width=True,
                     help="Clears the prompt only. Keeps images, faces and settings."):
            _clear_express(full=False)
            st.rerun()
    with _r2:
        if st.button("🧹 Full reset", key="ex_reset_btn", use_container_width=True,
                     help="Clears prompts, uploaded images, faces and references. Your videos stay below."):
            _clear_express(full=True)
            st.rerun()
    with _r3:
        st.caption("💡 After a video is ready you can just edit the prompt and press Generate again — "
                   "no reset needed. All videos from this session stay listed below.")

    ex_engine = st.radio(
        "Video engine",
        ["🎬 Seedance 2.0 — stable (15s per take)",
         "🚀 Seedance 2.5 — NEW: 30s in a single take, better consistency"],
        index=0, horizontal=True, key="ex_engine",
        help="2.5 generates up to 30s in one take (no stitching!) and improves timing/consistency. "
             "If your ModelArk account doesn't have 2.5 access yet you'll get a clear message — switch back to 2.0.",
    )
    # Longest clip a single generation can make on the chosen engine
    _single_take_max = 30 if ex_engine.startswith("🚀") else 15
    def _dur_label(x):
        if x < 4:
            return f"{x}s · short (generated at 4s, auto-trimmed)"
        if x <= _single_take_max:
            return f"{x}s" + (" · single take ✓" if x > 15 else "")
        n = (x + _single_take_max - 1) // _single_take_max
        return f"{x}s (×{n} chunks, stitched)"

    col_n, col_d, col_r, col_q = st.columns([1, 1, 1, 1])
    with col_q:
        _res_opts = (["480p", "720p", "1080p"] if _single_take_max == 30
                     else ["720p", "1080p", "4k"])
        _res_labels = {
            "480p": "480p — draft / cheapest",
            "720p": "720p — fast and cheap (default)",
            "1080p": "1080p — Full HD",
            "4k": "4K — maximum quality (expensive/slow)",
        }
        ex_resolution = st.selectbox(
            "Video quality",
            _res_opts,
            index=_res_opts.index("720p"),
            key="ex_res",
            format_func=lambda x: _res_labels[x],
            help=("Options follow the selected engine. Higher resolutions cost more "
                  "credits and take longer. If the API rejects a resolution, step down one level."),
        )
    with col_n:
        ex_n = st.number_input(
            "How many videos to create?",
            min_value=1, max_value=50, value=1, step=1, key="ex_n",
        )
    with col_d:
        ex_default_dur = st.selectbox(
            "Duration (seconds)",
            [2, 3, 4, 5, 8, 10, 15, 20, 25, 30, 40, 45, 60], index=6,
            format_func=_dur_label,
            key="ex_dur",
        )
    with col_r:
        ex_default_ratio = st.selectbox(
            "Aspect ratio",
            ["adaptive", "9:16", "16:9", "1:1", "4:3", "3:4", "21:9"],
            index=1,
            format_func=lambda x: {
                "adaptive": "🤖 Auto (based on the reference)",
                "9:16": "📱 9:16 — vertical (TikTok/Reels)",
                "16:9": "🖥 16:9 — horizontal (YouTube/CTV)",
                "1:1": "⏹ 1:1 — square (Instagram feed)",
                "4:3": "📺 4:3 — classic",
                "3:4": "📐 3:4 — classic portrait",
                "21:9": "🎬 21:9 — cinematic",
            }[x],
            key="ex_ratio",
        )

    ex_gen_audio = st.checkbox(
        "🔊 Generate audio (Seedance adds voice/dialogue)",
        value=True,
        key="ex_gen_audio",
        help=(
            "Turn off if Seedance refuses to generate the video with the error "
            "'OutputAudioSensitiveContentDetected'. The video will be generated without audio."
        ),
    )
    st.checkbox(
        "🎵 No background music (recommended — prevents copyright blocks)",
        value=True, key="ex_no_music",
        help="When the prompt doesn't describe the sound, Seedance invents its own soundtrack, "
             "and that music is sometimes blocked as copyrighted. This tells Seedance to use only "
             "natural sound and voice. Turn off if your prompt describes the music you want.",
    )

    st.markdown("**🖼 Product images (optional — up to 9)**")
    ex_uploaded = st.file_uploader(
        "If the prompt mentions Image 1 / Image 2 — uploading is required. Otherwise optional.",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key=f"ex_uploader_{st.session_state.get('_ex_gen', 0)}",
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
                f"✂️ Using the **{len(ex_image_paths)} auto-split variants** instead of the original image. "
                "Want to start over? Click '🧹 Full reset' above."
            )

        # ── If multi-angle reference sheets were generated, use them instead ──
        _cur_sig = "|".join(ex_image_paths)
        if (st.session_state.get("_sheets_src_sig") == _cur_sig
                and st.session_state.get("sheet_variant_paths")
                and all(Path(sp_).exists() for sp_ in st.session_state["sheet_variant_paths"])):
            ex_image_paths = list(st.session_state["sheet_variant_paths"])
            st.session_state["image_paths"] = ex_image_paths
            st.session_state["image_path"] = ex_image_paths[0]
            st.session_state["_sheets_active"] = True
            st.info(
                f"🖼 Using the **{len(ex_image_paths)} auto-generated multi-angle reference sheets**. "
                "To go back to the original images: '🧹 Full reset'."
            )
        else:
            st.session_state["_sheets_active"] = False

        # ── Auto variant splitter: one group photo → separate variants ──
        if len(ex_image_paths) == 1 and not st.session_state.get("_sheets_active"):
            with st.expander("✂️ Does the image show several colors together? Auto-split into separate images", expanded=True):
                st.caption(
                    "If the image shows several variants of the product together (e.g. a pile of rings in 7 colors) — "
                    "one click: Gemini detects each color, creates a clean product image on a white background for each, "
                    "and names them automatically. You end up with a separate @Image per color + the generator opens on its own."
                )
                try:
                    from nano_banana import is_available as _nb_ok
                    _nb_available = _nb_ok()
                except Exception:
                    _nb_available = False
                if not _nb_available:
                    st.warning("GEMINI_API_KEY is missing in Secrets — required for auto-splitting.")
                elif st.button("✂️ Auto-split into variants", type="primary",
                                use_container_width=True, key="ex_split_btn"):
                    import importlib as _il
                    import variant_splitter as _vs
                    _il.reload(_vs)
                    with st.status("✂️ Splitting variants...", expanded=True) as _sp:
                        try:
                            _names = _vs.detect_variants(ex_image_paths[0], log=_sp.write)
                            if len(_names) < 2:
                                _sp.update(label="Only one variant detected — nothing to split", state="complete")
                            else:
                                _sp.write(f"✓ Detected {len(_names)} variants: " + ", ".join(_names))
                                _results = _vs.extract_variants(
                                    ex_image_paths[0], _names,
                                    save_dir / "variants", log=_sp.write,
                                )
                                st.session_state["split_variant_paths"] = [r_[0] for r_ in _results]
                                st.session_state["split_variant_roles"] = [r_[1] for r_ in _results]
                                _sp.update(label=f"✅ Created {len(_results)} separate named images", state="complete")
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
                "🏷 **Role for each image (recommended)** — helps you write a prompt that combines "
                "several products/components in one video without confusion."
            )

            # Auto-name: one Gemini call fills all role fields on first upload
            _roles_empty = not any(
                (st.session_state.get(f"ex_img_role_{_i}") or "").strip()
                for _i in range(len(ex_image_paths))
            )
            _paths_sig = "|".join(ex_image_paths)
            if _roles_empty and st.session_state.get("_autoname_sig") != _paths_sig:
                st.session_state["_autoname_sig"] = _paths_sig
                try:
                    from nano_banana import is_available as _nb_ok2
                    if _nb_ok2():
                        import importlib as _il2
                        import variant_splitter as _vs2
                        _il2.reload(_vs2)
                        with st.spinner("🤖 Gemini is detecting the colors and naming them automatically..."):
                            _auto_names = _vs2.name_images(ex_image_paths)
                        for _i, _n in enumerate(_auto_names):
                            if _n:
                                st.session_state[f"ex_img_role_{_i}"] = _n
                        st.toast(f"✅ Auto-detected {sum(1 for n_ in _auto_names if n_)} names")
                except Exception as _e:
                    st.caption(f"⚠ Auto-detection failed ({_e}) — you can fill in manually.")

            ex_roles = []
            role_cols = st.columns(min(len(ex_image_paths), 3))
            for idx in range(len(ex_image_paths)):
                with role_cols[idx % 3]:
                    r = st.text_input(
                        f"@Image {idx+1}",
                        key=f"ex_img_role_{idx}",
                        placeholder="e.g.: bottle - front / component / packaging",
                    )
                    ex_roles.append(r.strip())
            st.session_state["image_roles"] = ex_roles
            tagged = [f"@Image {i+1} = {r}" for i, r in enumerate(ex_roles) if r]
            if tagged:
                st.info(
                    "📋 **Reference map for the prompt** — copy into the prompt and anchor each beat to the right image:\n\n"
                    + "\n".join(f"- `{t}`" for t in tagged)
                    + "\n\nExample: *\"[00:00] she holds @Image 1 ... [00:05] close-up on @Image 2 next to it — "
                    "all references must remain visually unchanged across cuts.\"*"
                )
        else:
            st.session_state["image_roles"] = []

            # ── Reference sheet for a single product image ──
            with st.expander("🖼 Create a multi-angle Reference Sheet for the image (recommended!)",
                              expanded=not st.session_state.get("_sheets_active")):
                st.caption(
                    "Nano Banana turns your image into one image with 6 panels — front, both profiles, "
                    "top-down, macro (thickness visible), and worn on the hand — and swaps it in automatically. "
                    "This way Seedance understands the true shape from every angle and the product doesn't come out warped."
                )
                _single_mode = st.radio(
                    "Product type",
                    ["💍 Worn on a finger (ring)", "🤲 Held in hand (any other product)"],
                    index=0, horizontal=True, key="ex_sheet_mode_1",
                )
                _smode1 = "ring" if _single_mode.startswith("💍") else "held"
                if not st.session_state.get("_sheets_active"):
                    if st.button("🚀 Create Reference Sheet and use it", type="primary",
                                  use_container_width=True, key="ex_sheets_btn_1"):
                        from nano_banana import generate_scene_image as _gen1
                        _src_sig1 = "|".join(ex_image_paths)
                        with st.status("🖼 Creating Reference Sheet...", expanded=True) as _sh1:
                            try:
                                _out1 = save_dir / "sheets" / "sheet_single.png"
                                _gen1(build_product_asset_sheet_prompt("", _smode1),
                                      [ex_image_paths[0]], _out1, log=_sh1.write)
                                st.session_state["sheet_variant_paths"] = [str(_out1)]
                                st.session_state["_sheets_src_sig"] = _src_sig1
                                _sh1.update(label="✅ Reference Sheet created and swapped in automatically", state="complete")
                                st.rerun()
                            except Exception as _e1:
                                _sh1.update(label=f"❌ {_e1}", state="error", expanded=True)
                    with st.expander("👁 The prompt (for manual use in an external generator)", expanded=False):
                        st.code(build_product_asset_sheet_prompt("", _smode1), language=None)
                else:
                    st.success(
                        "✅ The Reference Sheet is active — the video will be generated from it. "
                        "Prompt tip: add the line — "
                        "*\"@Image 1 is a multi-angle reference sheet of the product — "
                        "match its exact shape, thickness and proportions from every angle.\"*"
                    )

        # ── Auto prompt generator: one UGC video that shows ALL products ──
        if len(ex_image_paths) > 1:
            with st.expander("🪄 Auto generator: one UGC prompt that shows all the products", expanded=True):
                st.caption(
                    f"You uploaded {len(ex_image_paths)} images — one click builds a ready prompt where the character "
                    "talks about all the variants and shows each one, one after another, with all the consistency rules."
                )
                gen_mode = st.radio(
                    "How is each product shown?",
                    ["💍 Worn on a finger (rings)", "🤲 Held in hand (any other product)"],
                    index=0, horizontal=True, key="ex_gen_mode",
                )
                gen_size = ""
                if gen_mode.startswith("🤲"):
                    gen_size = st.text_input(
                        "Real product size (in English — important for proportions!)",
                        key="ex_gen_size",
                        placeholder="e.g. a 25cm tall bottle / a palm-sized jar / a 10cm box",
                    )
                # Duration = the one setting at the top (no second control).
                gen_dur = int(ex_default_dur)
                _per_variant = max(1, (int(gen_dur) - 4) // max(1, len(ex_image_paths)))
                st.caption(
                    f"⏱ At {int(gen_dur)} seconds, each of the {len(ex_image_paths)} colors gets ~{_per_variant} seconds of screen time"
                    + (" — very short; consider 20-25s or fewer colors." if _per_variant < 2 else ".")
                )
                gen_prompt = build_multi_product_ugc_prompt(
                    len(ex_image_paths),
                    st.session_state.get("image_roles", []),
                    int(gen_dur),
                    wear_mode="ring" if gen_mode.startswith("💍") else "held",
                    size_desc=gen_size,
                    sheets_active=bool(st.session_state.get("_sheets_active")),
                )
                if st.button("🪄 Build a prompt for all products → Video #1", type="primary",
                              use_container_width=True, key="ex_gen_btn"):
                    st.session_state["ex_prompt_0"] = gen_prompt
                    st.success("✅ The prompt was placed into Video #1 below — you can edit it, then scroll to Stage 4 to generate.")

                # Premium path: Claude (Opus) writes the prompt with the full
                # skill ruleset AND sees the actual product images.
                try:
                    from anthropic_client import is_available as _cl_ok
                    _claude_ok = _cl_ok()
                except Exception:
                    _claude_ok = False
                if _claude_ok:
                    if st.button("🧠 Let Claude write the prompt (sees the images — maximum quality)",
                                  use_container_width=True, key="ex_claude_btn"):
                        from anthropic_client import call_claude_api
                        from prompt_generator import SKILL_INSTRUCTIONS
                        from stage3_prompts import MULTI_PRODUCT_RULES, parse_prompt_from_response
                        _rules = MULTI_PRODUCT_RULES.replace("{n}", str(len(ex_image_paths)))
                        _roles_txt = "\n".join(
                            f"@Image {i_+1} = {r_}"
                            for i_, r_ in enumerate(st.session_state.get("image_roles", [])) if r_
                        ) or "(no labels — infer each variant color from its attached image, in order)"
                        _is_ring = gen_mode.startswith("💍")
                        _msg = (
                            f"Write ONE Seedance 2.0 UGC video prompt.\n\n"
                            f"PRODUCT VARIANTS ({len(ex_image_paths)} reference images attached, in upload order):\n"
                            f"{_roles_txt}\n\n"
                            f"PARAMETERS:\n"
                            f"- Duration: {int(gen_dur)} seconds\n"
                            f"- Wear mode: {'worn on finger (slim silicone ring, ~2cm)' if _is_ring else 'handheld product'}\n"
                            + ("- Each @Image is a multi-angle reference sheet of ONE variant.\n"
                               if st.session_state.get("_sheets_active")
                               else "- Each @Image is one product photo of ONE variant.\n")
                            + ("" if _is_ring else f"- Real physical size: {gen_size or 'state realistic proportions vs hands'}\n")
                            + f"- The video must SHOW ALL {len(ex_image_paths)} variants one at a time per the protocol below.\n\n"
                            f"{_rules}\n\n"
                            "OUTPUT: ONE fenced code block containing ONLY the prompt. No commentary."
                        )
                        with st.spinner("🧠 Claude is looking at the images and writing the prompt..."):
                            try:
                                _resp = call_claude_api(
                                    _msg, attachments=list(ex_image_paths),
                                    system=SKILL_INSTRUCTIONS, max_tokens=4000,
                                )
                                st.session_state["ex_prompt_0"] = parse_prompt_from_response(_resp)
                                st.success("✅ Claude's prompt was placed into Video #1 below — scroll down to review and edit.")
                            except Exception as _e:
                                st.error(f"Claude failed: {_e}")
                with st.expander("👁 Prompt preview", expanded=False):
                    st.code(gen_prompt, language=None)

            # ── Multi-angle reference sheets: one image per variant, all sides ──
            with st.expander("🖼 Multi-angle image generator (a Reference Sheet per color)", expanded=False):
                st.caption(
                    "For each variant we build a prompt for **Seedream 5.0 / Nano Banana**: one image with 6 panels — "
                    "front, both profiles, top-down, macro, and worn on the hand. Paste the prompt into the image generator "
                    "**with the original image attached**, then upload the result back here in place of the original image — "
                    "this way Seedance gets every angle of each ring in a single image and can animate it from any direction."
                )
                sheet_mode = "ring" if st.session_state.get("ex_gen_mode", "💍").startswith("💍") else "held"
                roles_now = st.session_state.get("image_roles", [])

                # One-click: Nano Banana builds ALL the sheets and swaps them in
                if not st.session_state.get("_sheets_active"):
                    if st.button("🚀 Auto-create all the reference sheets and use them (Nano Banana)",
                                  type="primary", use_container_width=True, key="ex_sheets_btn"):
                        from nano_banana import generate_scene_image as _gen_img
                        _src_sig = "|".join(ex_image_paths)
                        with st.status("🖼 Creating a multi-angle reference sheet for each variant...", expanded=True) as _sh:
                            try:
                                _new_paths = []
                                for _idx, _ip in enumerate(ex_image_paths):
                                    _lbl = roles_now[_idx] if _idx < len(roles_now) else ""
                                    _sh.write(f"🖼 {_idx+1}/{len(ex_image_paths)} — {_lbl or f'Image {_idx+1}'}")
                                    _out = save_dir / "sheets" / f"sheet_{_idx+1}.png"
                                    _gen_img(build_product_asset_sheet_prompt(_lbl, sheet_mode),
                                             [_ip], _out, log=_sh.write)
                                    _new_paths.append(str(_out))
                                st.session_state["sheet_variant_paths"] = _new_paths
                                st.session_state["_sheets_src_sig"] = _src_sig
                                _sh.update(label=f"✅ Created {len(_new_paths)} reference sheets — swapped in automatically", state="complete")
                                st.rerun()
                            except Exception as _e:
                                _sh.update(label=f"❌ {_e}", state="error", expanded=True)
                    st.caption("Or manually — copy the prompts below into an external image generator:")
                else:
                    st.success("✅ The reference sheets are active — the video will be generated from them.")
                for idx in range(len(ex_image_paths)):
                    label = roles_now[idx] if idx < len(roles_now) else ""
                    title = label if label else f"Image {idx+1}"
                    st.markdown(f"**@Image {idx+1} — {title}**")
                    st.code(build_product_asset_sheet_prompt(label, sheet_mode), language=None)

    _render_official_faces(project_root)

    # Old "upload your own AI face" fallback removed (blocked by the filter).
    st.session_state.pop("ai_char_paths", None)

    st.markdown("**🎥 Reference video (optional — up to 3, each ≤15 seconds)**")
    st.caption(
        "If you have an example video (a competitor's clip / another creator / an old video of yours) — "
        "upload it here, and the model will try to mimic its style/motion, just with your product and your character."
    )
    ex_video_refs = st.file_uploader(
        "MP4 only, up to 3 files",
        type=["mp4", "mov", "webm"],
        accept_multiple_files=True,
        key=f"ex_video_refs_{st.session_state.get('_ex_gen', 0)}",
    )
    st.checkbox(
        "🫥 Auto-blur faces in reference videos (bypasses Seedance's filter)",
        value=True,
        key="ex_blur_faces",
        help=(
            "Seedance blocks reference videos that contain real faces. "
            "This option auto-blurs faces before uploading — Seedance still learns "
            "the style, motion and composition (which is all it uses from the reference), "
            "and real faces are kept away from the filter. Turn off if the video is already people-free."
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
        st.success(f"✓ {len(ref_paths)} reference videos ready. They will be uploaded to catbox at generation time.")
    else:
        st.session_state.pop("ref_video_paths", None)

    st.markdown(f"**📝 Write {int(ex_n)} prompts** (each one separate):")
    if "_pending_prompt_0" in st.session_state:
        st.session_state["ex_prompt_0"] = st.session_state.pop("_pending_prompt_0")
        st.success("✏️ The prompt was loaded into Video #1 — tweak it and generate again.")
    ex_prompts = []
    for i in range(int(ex_n)):
        with st.expander(f"Video #{i+1}", expanded=(i == 0)):
            txt = st.text_area(
                f"Video prompt {i+1}",
                height=180,
                key=f"ex_prompt_{i}",
                placeholder=(
                    "Example: A 30-year-old woman in a sunlit kitchen, "
                    "holding Image 1, saying 'okay so I tried this for a week and...'. "
                    "Phone-quality footage, casual UGC vibe, 3-4 jump cuts, English audio."
                ),
                label_visibility="collapsed",
            )
            # Duration + aspect ratio come from the settings at the top.
            ex_prompts.append({
                "prompt": txt,
                "duration": int(ex_default_dur),
                "aspect_ratio": ex_default_ratio,
            })

    valid = [p for p in ex_prompts if p["prompt"].strip()]

    # AUTO-SAVE — every rerun, push the latest prompts into stage3.
    # The user doesn't have to click "Save" — what they see in the boxes is
    # what Stage 4 will generate. We always REPLACE any older data.
    if valid:
        _save_express_plan(valid, ex_gen_audio)
        st.success(
            f"\u2705 {len(valid)} active prompts out of {int(ex_n)}. "
            f"Scroll to '5\ufe0f\u20e3 Stage 4' to generate."
        )
    else:
        # No valid prompts — wipe Express plan so Stage 4 stays disabled.
        st.session_state.pop("stage3", None)
        st.session_state.pop("stage2", None)
        st.info(f"\U0001F4A1 Write a prompt in one of the {int(ex_n)} fields above.")

    st.markdown("---")
    st.caption("\u2B07 Scroll down to '5\ufe0f\u20e3 Stage 4' to generate the video.")
    st.markdown("---")
