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
  --left-w: clamp(560px, 62vw, 1180px);   /* create panel gets most of the screen */
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
    max-width: var(--left-w) !important; width: var(--left-w) !important;
    align-self: flex-start !important;            /* stMain centers its child — pin it left */
    margin-left: 16px !important; margin-right: 0 !important;
    padding-left: 0 !important; padding-right: 0 !important;
  }
  /* feed = responsive grid of compact cards; header rows span the full width */
  .st-key-asp_feed{
    display: grid !important; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
    gap: 14px !important; align-content: start; align-items: start;
  }
  .st-key-asp_feed > *{ grid-column: 1 / -1; }
  .st-key-asp_feed > *:has(> [class*="st-key-asp_card_"]){ grid-column: auto; }
  .st-key-asp_feed{
    position: fixed !important; top: 3rem; bottom: 14px;
    left: calc(var(--left-w) + 34px); right: 16px; width: auto !important;
    overflow-y: auto; overflow-x: hidden;
    background: var(--panel); border: 1px solid var(--line); border-radius: 18px;
    padding: 12px 12px; z-index: 5;
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
  width: 100% !important; max-height: 60vh !important; border-radius: 14px; background: #000; display:block;
}
[class*="st-key-asp_card_"] video{ max-height: 250px !important; aspect-ratio: 9/16; object-fit: contain; }
[data-testid="stSidebar"]{ background: var(--panel); border-right: 1px solid var(--line); }

/* ── top bar ────────────────────────────────────────────── */
.asp-top{ display:flex; align-items:center; gap:10px; margin: 0; }
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
  background: var(--bg); border: 1px solid var(--line); border-radius: 16px; padding: 10px;
  gap: 8px !important;
}
[class*="st-key-asp_card_"]:hover{ border-color: #34343b; }
.asp-tags{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom: 8px; }
.asp-tag{ font-size:.7rem; font-weight:600; padding: 2px 8px; border-radius: 999px;
  background: var(--panel2); border:1px solid var(--line); color:#cfcfd4; }
.asp-tag.engine{ color: var(--accent); border-color: rgba(200,245,96,.35); }
.asp-prompt{
  font-size:.82rem; line-height:1.5; color:#bdbdc4; white-space: pre-wrap;
  max-height: 4.5em; overflow-y: auto; font-size: .74rem !important; padding-right: 4px; margin-bottom: 10px;
}
.asp-empty{
  border: 1px dashed #2e2e34; border-radius: 16px; padding: 48px 20px; text-align:center; color: var(--muted);
}
.asp-empty b{ display:block; color: var(--text); font-size: 1rem; margin-bottom: 6px; }
.st-key-asp_feed .asp-tag{ font-size:.62rem; padding:1px 6px; }
[class*="st-key-asp_card_"] .stButton > button, [class*="st-key-asp_card_"] .stDownloadButton > button,
[class*="st-key-asp_card_"] .stLinkButton > a{ min-height: 1.9rem; font-size: .74rem; padding: 0 6px; }
[class*="st-key-asp_card_"]{ padding: 7px !important; gap: 6px !important; }
</style>
"""


def inject_theme() -> None:
    """Inject the global CSS. Call once, right after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


_LIGHT_CSS = """
<style>
:root{
  --bg:#F5F5F7; --panel:#FFFFFF; --panel2:#F0F0F3; --line:#E1E1E7;
  --text:#141417; --muted:#6A6A74; --accent:#C8F560; --accent-ink:#0A0A0B;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"]{
  background: var(--bg) !important; color: var(--text) !important;
}
.stApp p, .stApp li, .stApp h1, .stApp h3, .stApp span, .stApp label,
[data-testid="stMarkdownContainer"], [data-testid="stExpander"] summary,
[data-testid="stFileUploaderDropzone"] *, .stApp input, .stApp textarea,
[data-baseweb="select"] div{ color: var(--text) !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *,
[data-testid="stWidgetLabel"] p{ color: var(--muted) !important; }
.stApp input::placeholder, .stApp textarea::placeholder{ color:#9a9aa3 !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"]{
  background: #fff !important; color: var(--text) !important;
}
[data-baseweb="popover"] li:hover{ background: var(--panel2) !important; }
.stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover{
  background:#E8E8EC !important; color: var(--text) !important; border-color:#cfcfd6 !important;
}
.stButton > button[kind="primary"]:disabled{ background:#E4E4E8 !important; color:#9a9aa3 !important; }
.asp-tag{ color:#3a3a42 !important; }
.asp-tag.engine{ color:#3F6212 !important; border-color:#bfe38a !important; background:#F4FBE6 !important; }
.asp-prompt{ color:#4a4a52 !important; }
[class*="st-key-asp_card_"]{ background:#FFFFFF !important; }
.st-key-asp_feed{ background: var(--panel2) !important; }
.st-key-asp_feed::-webkit-scrollbar-thumb{ background:#cfcfd6 !important; }
[data-testid="stAlert"]{ background:#fff !important; }
[data-testid="stSidebar"]{ background:#fff !important; }
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked){ background:#F4FBE6 !important; }
</style>
"""


def _theme_is_light() -> bool:
    try:
        if "asp_light" not in st.session_state:
            st.session_state["asp_light"] = st.query_params.get("theme") == "light"
    except Exception:
        st.session_state.setdefault("asp_light", False)
    return bool(st.session_state.get("asp_light"))


def render_topbar(user_email: str = "") -> None:
    _theme_is_light()
    c_bar, c_tg = st.columns([6, 1.3], vertical_alignment="center")
    with c_bar:
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
    with c_tg:
        light = st.toggle("☀️ Light", key="asp_light",
                          help="Switch the whole site between dark and light")
    try:
        if light:
            st.query_params["theme"] = "light"
        elif st.query_params.get("theme"):
            del st.query_params["theme"]
    except Exception:
        pass
    if light:
        st.markdown(_LIGHT_CSS, unsafe_allow_html=True)


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
