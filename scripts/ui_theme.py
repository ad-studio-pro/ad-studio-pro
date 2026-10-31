"""
UI theme v3 — "studio" layout for Ad Studio Pro.

Design language (inspired by modern AI-video studios):
  • near-black surfaces, soft 1px borders, rounded 14px panels
  • a narrow CREATE panel on the left, the RESULTS FEED on the right
    (the feed is a st.container(key="asp_feed") pinned with CSS)
  • small muted labels, compact controls, ONE bright Generate button

Usage (app.py, right after st.set_page_config):
    inject_theme(); render_topbar(email)
"""

import streamlit as st

ACCENT = "#C8F560"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root{
  --bg:#0A0A0B; --panel:#131315; --panel2:#1A1A1D; --line:#26262B;
  --text:#F2F2F3; --muted:#8C8C95; --accent:#C8F560; --accent-ink:#0A0A0B;
  --left-w: 540px;
}
html, body, [data-testid="stAppViewContainer"] * {
  font-family: 'Inter', 'Segoe UI', sans-serif;
}
/* keep Streamlit's icon fonts working */
span[data-testid="stIconMaterial"], [data-testid="stIconMaterial"],
.material-icons, [class^="material-symbols"], [class*=" material-symbols"] {
  font-family: 'Material Symbols Outlined','Material Symbols Rounded','Material Icons' !important;
}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: var(--bg); }
[data-testid="stHeader"] { height: 2.6rem; }

/* ── page frame ─────────────────────────────────────────── */
[data-testid="stMainBlockContainer"], .block-container {
  padding-top: 3rem !important; padding-bottom: 3rem;
}
/* STUDIO LAYOUT: when the feed exists, the main column becomes the left panel */
@media (min-width: 1100px){
  [data-testid="stMainBlockContainer"]:has(.st-key-asp_feed),
  .block-container:has(.st-key-asp_feed){
    max-width: var(--left-w) !important; margin-left: 16px !important; margin-right: 0 !important;
    padding-left: 0 !important; padding-right: 0 !important;
  }
  .st-key-asp_feed{
    position: fixed !important; top: 3rem; bottom: 14px;
    left: calc(var(--left-w) + 34px); right: 16px; width: auto !important;
    overflow-y: auto; overflow-x: hidden;
    background: var(--panel); border: 1px solid var(--line); border-radius: 18px;
    padding: 16px 18px; z-index: 5;
  }
  .st-key-asp_feed::-webkit-scrollbar{ width: 8px; }
  .st-key-asp_feed::-webkit-scrollbar-thumb{ background:#2a2a30; border-radius: 8px; }
}
@media (max-width: 1099px){
  .st-key-asp_feed{ border-top:1px solid var(--line); margin-top: 18px; padding-top: 12px; }
}

/* ── typography ─────────────────────────────────────────── */
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] li { font-size: .92rem; }
[data-testid="stWidgetLabel"] p, [data-testid="stAppViewContainer"] label p {
  font-size: .78rem !important; color: var(--muted) !important; font-weight: 500;
  letter-spacing: .01em;
}
[data-testid="stCaptionContainer"] { color: var(--muted); font-size: .8rem; }
[data-testid="stAppViewContainer"] h1 { font-size: 1.25rem; font-weight: 700; }
[data-testid="stAppViewContainer"] h2 {
  font-size: .78rem !important; font-weight: 700 !important; text-transform: uppercase;
  letter-spacing: .08em; color: var(--muted) !important;
  margin: 1.4rem 0 .4rem !important; padding: 0 !important; background: none !important; border: 0 !important;
}
[data-testid="stAppViewContainer"] h3 { font-size: 1rem; font-weight: 700; }
hr { border-color: var(--line) !important; margin: .9rem 0 !important; }

/* ── panels (expanders) ─────────────────────────────────── */
[data-testid="stExpander"] details{
  background: var(--panel); border: 1px solid var(--line) !important; border-radius: 14px !important;
}
[data-testid="stExpander"]{ margin-bottom: .5rem; }
[data-testid="stExpander"] summary{ font-weight: 600; font-size: .9rem; padding: .7rem .9rem; }
[data-testid="stExpander"] summary:hover{ color: var(--accent); }

/* ── inputs ─────────────────────────────────────────────── */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"],
[data-testid="stNumberInput"] input, textarea {
  background: var(--panel2) !important; border-color: var(--line) !important; border-radius: 12px !important;
}
textarea { font-size: .92rem !important; line-height: 1.5 !important; }
[data-baseweb="select"] > div:hover, [data-baseweb="input"]:hover, [data-baseweb="textarea"]:hover{
  border-color: #3a3a42 !important;
}
[data-testid="stFileUploaderDropzone"]{
  background: var(--panel2); border: 1px dashed #34343b; border-radius: 14px;
}
[data-testid="stFileUploaderDropzone"]:hover{ border-color: var(--accent); }
/* radios as pills */
[data-testid="stRadio"] [role="radiogroup"]{ gap: 6px; flex-wrap: wrap; }
[data-testid="stRadio"] [role="radiogroup"] > label{
  background: var(--panel2); border: 1px solid var(--line); border-radius: 999px;
  padding: 5px 12px 5px 8px; margin: 0 !important;
}
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked){
  border-color: var(--accent); background: rgba(200,245,96,.08);
}
[data-testid="stRadio"] [role="radiogroup"] > label p{ font-size: .82rem !important; color: var(--text) !important; }

/* ── buttons ────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button, .stLinkButton > a{
  border-radius: 12px; font-weight: 600; font-size: .86rem; min-height: 2.4rem;
  background: var(--panel2); border: 1px solid var(--line); color: var(--text);
  transition: all .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover{
  border-color: #44444c; color: #fff; background: #202024;
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"]{
  background: var(--accent) !important; color: var(--accent-ink) !important; border: none !important;
  font-weight: 800; font-size: 1rem; min-height: 3rem; letter-spacing: .02em;
  box-shadow: 0 6px 24px rgba(200,245,96,.18);
}
.stButton > button[kind="primary"] p{ color: var(--accent-ink) !important; font-weight: 800; }
.stButton > button[kind="primary"]:hover{ filter: brightness(1.06); transform: translateY(-1px); }
.stButton > button[kind="primary"]:disabled{ background:#2a2a2f !important; color:#666 !important; box-shadow:none; }

/* ── alerts, status, video ──────────────────────────────── */
[data-testid="stAlert"]{ border-radius: 12px; border: 1px solid var(--line); }
[data-testid="stStatusWidget"], [data-testid="stExpander"] [data-testid="stStatus"]{ border-radius: 12px; }
[data-testid="stVideo"] video, video{
  width: 100% !important; max-height: 70vh !important; border-radius: 14px; background: #000; display:block;
}
[data-testid="stSidebar"]{ background: var(--panel); border-right: 1px solid var(--line); }

/* ── top bar ────────────────────────────────────────────── */
.asp-top{ display:flex; align-items:center; gap:10px; margin: 0 0 14px; }
.asp-logo{
  width:30px; height:30px; border-radius:9px; background: var(--accent); color: var(--accent-ink);
  display:flex; align-items:center; justify-content:center; font-weight:900; font-size:.9rem;
}
.asp-brand{ font-weight:800; font-size:1.05rem; letter-spacing:-.01em; }
.asp-chip{
  font-size:.7rem; font-weight:600; color: var(--muted); border:1px solid var(--line);
  padding: 2px 9px; border-radius: 999px; background: var(--panel);
}
.asp-user{ margin-left:auto; font-size:.75rem; color: var(--muted); }

/* ── feed cards ─────────────────────────────────────────── */
.asp-feed-head{ display:flex; align-items:baseline; gap:10px; margin-bottom: 4px; }
.asp-feed-head .t{ font-size:1.05rem; font-weight:800; }
.asp-feed-head .c{ font-size:.78rem; color: var(--muted); }
[class*="st-key-asp_card_"]{
  background: var(--bg); border: 1px solid var(--line); border-radius: 16px; padding: 12px;
  margin-bottom: 12px;
}
[class*="st-key-asp_card_"]:hover{ border-color: #34343b; }
.asp-tags{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom: 8px; }
.asp-tag{ font-size:.7rem; font-weight:600; padding: 2px 8px; border-radius: 999px;
  background: var(--panel2); border:1px solid var(--line); color:#cfcfd4; }
.asp-tag.engine{ color: var(--accent); border-color: rgba(200,245,96,.35); }
.asp-prompt{
  font-size:.82rem; line-height:1.5; color:#bdbdc4; white-space: pre-wrap;
  max-height: 11.5em; overflow-y: auto; padding-right: 4px; margin-bottom: 10px;
}
.asp-empty{
  border: 1px dashed #2e2e34; border-radius: 16px; padding: 48px 20px; text-align:center; color: var(--muted);
}
.asp-empty b{ display:block; color: var(--text); font-size: 1rem; margin-bottom: 6px; }
</style>
"""


def inject_theme() -> None:
    """Inject the global CSS. Call once, right after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_topbar(user_email: str = "") -> None:
    user = f'<span class="asp-user">{user_email}</span>' if user_email else ""
    st.markdown(
        f"""
<div class="asp-top">
  <div class="asp-logo">A</div>
  <div class="asp-brand">Ad Studio Pro</div>
  <span class="asp-chip">Seedance 2.0 · 2.5</span>
  {user}
</div>
""",
        unsafe_allow_html=True,
    )


# Backward-compat: older code calls render_hero
def render_hero(user_email: str = "") -> None:
    render_topbar(user_email)


def render_stepper(steps) -> None:
    """Pipeline progress pills (Full pipeline only)."""
    items = []
    for i, (label, state) in enumerate(steps, 1):
        icon = "✓" if state == "done" else str(i)
        items.append(f'<span class="asp-tag">{icon} · {label}</span>')
    st.markdown(f'<div class="asp-tags">{"".join(items)}</div>', unsafe_allow_html=True)


def compute_full_pipeline_steps(ss) -> list:
    """Derive stepper states from st.session_state for the Full pipeline."""
    has_img = bool(ss.get("image_paths") or ss.get("image_path"))
    flags = [has_img, bool(ss.get("stage1")), bool(ss.get("stage2")),
             bool(ss.get("stage3")), bool(ss.get("stage4") or ss.get("video_results"))]
    labels = ["Upload product", "Research", "Plan", "Prompts", "Video ready"]
    steps, current_set = [], False
    for label, done in zip(labels, flags):
        if done:
            steps.append((label, "done"))
        elif not current_set:
            steps.append((label, "current"))
            current_set = True
        else:
            steps.append((label, "todo"))
    return steps
