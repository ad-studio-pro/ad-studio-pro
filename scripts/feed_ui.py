"""
Results feed — the right-hand panel of the studio layout.

Shows every MP4 in outputs/videos (newest first) as a card:
  [ video ]  [ engine · duration · ratio · time tags
               prompt (scrollable)
               ↻ Reuse prompt · ⬇ Download · 🔗 Link · 🗑 ]

Each generated video gets a JSON sidecar (<name>.json) with its prompt and
settings, written by app.py at generation time (save_meta). Older videos
without a sidecar still show — just without the prompt.
"""

import html
import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

PAGE = 6


def save_meta(video_path, **meta) -> None:
    """Write the sidecar next to a finished video. Never raises."""
    try:
        p = Path(video_path)
        meta.setdefault("created", datetime.now().strftime("%Y-%m-%d %H:%M"))
        p.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    except Exception:
        pass


def _load_meta(p: Path) -> dict:
    side = p.with_suffix(".json")
    if side.exists():
        try:
            return json.loads(side.read_text(encoding="utf-8"))
        except Exception:
            pass
    for h in st.session_state.get("video_history") or []:
        if isinstance(h, dict) and h.get("path") == str(p):
            return {"prompt": h.get("prompt", "")}
    return {}


def _clean_prompt(pr: str) -> str:
    return pr.split("\n\nSoundtrack rule:")[0].split("\n\nAudio: no background music")[0]


def _safe_key(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def render_feed(outputs_dir: Path, upload_video=None) -> None:
    vdir = Path(outputs_dir) / "videos"
    vids = sorted(vdir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True) if vdir.exists() else []

    with st.container(key="asp_feed"):
        st.markdown(
            f'<div class="asp-feed-head"><span class="t">Your videos</span>'
            f'<span class="c">{len(vids)} on the server · newest first</span></div>',
            unsafe_allow_html=True)
        if vids:
            st.caption("⚠ Server storage is temporary — download anything you want to keep.")

        if not vids:
            st.markdown(
                '<div class="asp-empty"><b>No videos yet</b>'
                'Write a prompt on the left and press Generate — your videos appear here.</div>',
                unsafe_allow_html=True)
            return

        n = int(st.session_state.get("_feed_n", PAGE))
        url_cache = st.session_state.setdefault("_video_share_urls", {})

        for p in vids[:n]:
            meta = _load_meta(p)
            k = _safe_key(p.stem)
            with st.container(key=f"asp_card_{k}"):
                c_vid, c_info = st.columns([1.25, 1], gap="medium")
                with c_vid:
                    st.video(str(p))
                with c_info:
                    when = meta.get("created") or datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    tags = []
                    if meta.get("engine"):
                        tags.append(f'<span class="asp-tag engine">Seedance {html.escape(str(meta["engine"]))}</span>')
                    for key, suf in (("duration", "s"), ("aspect_ratio", ""), ("resolution", "")):
                        if meta.get(key):
                            tags.append(f'<span class="asp-tag">{html.escape(str(meta[key]))}{suf}</span>')
                    tags.append(f'<span class="asp-tag">{html.escape(when)}</span>')
                    tags.append(f'<span class="asp-tag">{p.stat().st_size / 1048576:.1f} MB</span>')
                    st.markdown(f'<div class="asp-tags">{"".join(tags)}</div>', unsafe_allow_html=True)

                    prompt = _clean_prompt(meta.get("prompt", "") or "")
                    if prompt:
                        st.markdown(f'<div class="asp-prompt">{html.escape(prompt)}</div>',
                                    unsafe_allow_html=True)
                        if st.button("↻  Reuse prompt", key=f"fr_{k}", use_container_width=True,
                                     help="Loads this prompt into Video #1 so you can tweak it and generate again."):
                            st.session_state["_pending_prompt_0"] = prompt
                            st.rerun()
                    else:
                        st.caption(p.name)

                    b1, b2, b3 = st.columns([1, 1, 0.55])
                    with b1:
                        # read bytes only for the visible cards
                        st.download_button("⬇ Download", p.read_bytes(), file_name=p.name,
                                           mime="video/mp4", key=f"fd_{k}", use_container_width=True)
                    with b2:
                        if str(p) in url_cache:
                            st.link_button("🔗 Open link", url_cache[str(p)], use_container_width=True)
                        elif upload_video and st.button("🔗 Link", key=f"fl_{k}", use_container_width=True,
                                                         help="Uploads to a public host and gives a direct link"):
                            with st.spinner("Uploading…"):
                                try:
                                    url_cache[str(p)] = upload_video(p)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Upload error: {e}")
                    with b3:
                        ask = f"fdel_{k}"
                        if st.session_state.get(ask):
                            if st.button("✔", key=f"fdy_{k}", type="primary", help="Delete permanently",
                                         use_container_width=True):
                                try:
                                    p.unlink()
                                    p.with_suffix(".json").unlink(missing_ok=True)
                                except Exception as e:
                                    st.error(str(e))
                                st.session_state.pop(ask, None)
                                st.rerun()
                        elif st.button("🗑", key=f"fdb_{k}", help="Delete from the server",
                                       use_container_width=True):
                            st.session_state[ask] = True
                            st.rerun()
                    if st.session_state.get(f"fdel_{k}"):
                        st.caption("Delete this video permanently? Press ✔ to confirm.")
                        if st.button("Cancel", key=f"fdn_{k}", use_container_width=True):
                            st.session_state.pop(f"fdel_{k}", None)
                            st.rerun()

        if len(vids) > n:
            if st.button(f"Show more ({len(vids) - n} older)", key="feed_more", use_container_width=True):
                st.session_state["_feed_n"] = n + PAGE
                st.rerun()

        # Bulk export for CapCut — built only on request (can be large)
        with st.expander("📦 Download several videos as one ZIP (for CapCut)", expanded=False):
            pick = st.slider("How many of the newest videos", 1, len(vids), min(len(vids), 6), key="zip_n")
            if st.button("Prepare ZIP", key="zip_go", use_container_width=True):
                import io
                import zipfile
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
                    lines = []
                    for p in vids[:pick]:
                        zf.write(p, p.name)
                        pr = _clean_prompt(_load_meta(p).get("prompt", "") or "")
                        if pr:
                            lines.append(f"=== {p.name} ===\n{pr}")
                    if lines:
                        zf.writestr("prompts.txt", "\n\n".join(lines))
                st.session_state["_zip_bytes"] = buf.getvalue()
            if st.session_state.get("_zip_bytes"):
                st.download_button("⬇ Download ZIP", st.session_state["_zip_bytes"],
                                   file_name="ad_studio_videos.zip", mime="application/zip",
                                   key="zip_dl", use_container_width=True)
