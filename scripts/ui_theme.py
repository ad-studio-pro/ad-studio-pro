"""
UI theme — global CSS injection for Ad Studio Pro.

Gives the Streamlit app a branded look:
  - Heebo font (Hebrew + Latin)
  - RTL layout for Hebrew labels, with smart bidi for mixed content
  - Card-style expanders, rounded buttons, gradient hero header
  - English prompts / code stay LTR automatically (unicode-bidi: plaintext)

Usage (app.py, right after st.set_page_config):
    from ui_theme import inject_theme, render_hero
    inject_theme()
    render_hero(user_email)
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;800&display=swap');

html, body, [data-testid="stAppViewContainer"] * {
    font-family: 'Heebo', 'Segoe UI', sans-serif;
}

/* ── RTL layout ─────────────────────────────────────────── */
[data-testid="stAppViewContainer"] .block-container,
[data-testid="stSidebar"] {
    direction: rtl;
    text-align: right;
}
/* Mixed Hebrew/English inputs: each line auto-detects its direction */
textarea, input[type="text"] {
    unicode-bidi: plaintext;
}
/* Code / prompts / dataframes stay LTR */
pre, code, [data-testid="stDataFrame"] {
    direction: ltr;
    text-align: left;
}
/* Checkbox + radio spacing in RTL */
[data-testid="stCheckbox"] label, [data-testid="stRadio"] label {
    direction: rtl;
}

/* ── Cards & controls ───────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 14px;
    background: rgba(22, 26, 40, 0.55);
    margin-bottom: 0.4rem;
}
.stButton > button, .stDownloadButton > button, .stLinkButton > a {
    border-radius: 10px;
    font-weight: 600;
    transition: all .15s ease;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%);
    border: none;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(139, 92, 246, 0.5);
}

/* ── Headers as step badges ─────────────────────────────── */
[data-testid="stAppViewContainer"] h2 {
    border-right: 4px solid #8B5CF6;
    padding-right: 12px;
    border-radius: 2px;
    font-weight: 800;
    margin-top: 1.6rem;
}

/* ── Hero header ────────────────────────────────────────── */
.asp-hero {
    direction: rtl;
    background: linear-gradient(120deg, rgba(139,92,246,.28) 0%, rgba(30,27,75,.55) 55%, rgba(11,14,23,0) 100%);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 18px;
    padding: 20px 26px 16px;
    margin-bottom: 1.2rem;
}
.asp-hero h1 {
    margin: 0 0 2px;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #C4B5FD, #F4F5F9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.asp-hero p {
    margin: 0;
    opacity: .75;
    font-size: .95rem;
}
.asp-hero .asp-badges { margin-top: 8px; }
.asp-hero span.asp-badge {
    display: inline-block;
    font-size: .75rem;
    font-weight: 600;
    padding: 2px 10px;
    margin-left: 6px;
    border-radius: 999px;
    background: rgba(139, 92, 246, 0.18);
    border: 1px solid rgba(139, 92, 246, 0.4);
    color: #C4B5FD;
}

/* Sidebar polish */
[data-testid="stSidebar"] {
    border-left: 1px solid rgba(139, 92, 246, 0.2);
}

/* Status / info boxes rounder */
[data-testid="stAlert"] { border-radius: 12px; }
</style>
"""


def inject_theme() -> None:
    """Inject the global CSS. Call once, right after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_hero(user_email: str = "") -> None:
    """Branded hero header replacing st.title()."""
    email_line = f" · ברוך הבא <b>{user_email}</b>" if user_email else ""
    st.markdown(
        f"""
<div class="asp-hero">
  <h1>🎬 Ad Studio Pro</h1>
  <p>מפעל קמפיינים Seedance 2.0 — מחקר → תכנית → פרומטים → וידאו{email_line}</p>
  <div class="asp-badges">
    <span class="asp-badge">Seedance 2.0</span>
    <span class="asp-badge">Seed Audio 1.0</span>
    <span class="asp-badge">עד 9 תמונות מוצר</span>
    <span class="asp-badge">רפרנס וידאו + אודיו</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
