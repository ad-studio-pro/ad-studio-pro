"""
UI theme v2 — global CSS + hero + pipeline stepper for Ad Studio Pro.

Goals: clear visual hierarchy, RTL Hebrew, obvious "where am I in the flow".

Usage (app.py, right after st.set_page_config):
    from ui_theme import inject_theme, render_hero, render_stepper
    inject_theme()
    render_hero(user_email)
    render_stepper([...])   # inside the Full-pipeline branch
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;800&display=swap');

html, body, [data-testid="stAppViewContainer"] * {
    font-family: 'Heebo', 'Segoe UI', sans-serif;
}
[data-testid="stAppViewContainer"] .block-container {
    padding-top: 1.2rem;
    max-width: 1200px;
}

/* ── RTL layout ─────────────────────────────────────────── */
[data-testid="stAppViewContainer"] .block-container,
[data-testid="stSidebar"] {
    direction: rtl;
    text-align: right;
}
textarea, input[type="text"] { unicode-bidi: plaintext; }
pre, code, [data-testid="stDataFrame"] { direction: ltr; text-align: left; }

/* ── Typography ─────────────────────────────────────────── */
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] label {
    font-size: 1rem;
}
[data-testid="stCaptionContainer"] { opacity: .8; }

/* ── Section headers = step cards ───────────────────────── */
[data-testid="stAppViewContainer"] h2 {
    background: linear-gradient(90deg, rgba(139,92,246,.16), rgba(139,92,246,0));
    border-right: 5px solid #8B5CF6;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 800;
    font-size: 1.35rem;
    margin-top: 2rem;
}
[data-testid="stAppViewContainer"] h3 { font-weight: 700; }

/* ── Cards & controls ───────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid rgba(148, 163, 184, .22);
    border-radius: 14px;
    background: rgba(22, 26, 40, .55);
    margin-bottom: .45rem;
}
[data-testid="stExpander"] summary { font-weight: 600; }

.stButton > button, .stDownloadButton > button, .stLinkButton > a {
    border-radius: 10px;
    font-weight: 700;
    min-height: 2.6rem;
    transition: all .15s ease;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%);
    border: none;
    box-shadow: 0 4px 14px rgba(139, 92, 246, .35);
    font-size: 1.05rem;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(139, 92, 246, .5);
}

[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stSidebar"] { border-left: 1px solid rgba(139,92,246,.2); }
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed rgba(139,92,246,.45);
    border-radius: 14px;
    background: rgba(139,92,246,.06);
}

/* ── Hero ───────────────────────────────────────────────── */
.asp-hero {
    direction: rtl;
    background: linear-gradient(120deg, rgba(139,92,246,.3) 0%, rgba(30,27,75,.6) 55%, rgba(11,14,23,0) 100%);
    border: 1px solid rgba(139,92,246,.3);
    border-radius: 18px;
    padding: 18px 24px 14px;
    margin-bottom: .8rem;
}
.asp-hero h1 {
    margin: 0 0 2px; font-size: 1.9rem; font-weight: 800;
    background: linear-gradient(90deg, #C4B5FD, #F4F5F9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.asp-hero p { margin: 0; opacity: .78; font-size: .95rem; }
.asp-hero span.asp-badge {
    display: inline-block; font-size: .74rem; font-weight: 600;
    padding: 2px 10px; margin-left: 6px; margin-top: 8px; border-radius: 999px;
    background: rgba(139,92,246,.18); border: 1px solid rgba(139,92,246,.4);
    color: #C4B5FD;
}

/* ── Stepper ────────────────────────────────────────────── */
.asp-stepper {
    direction: rtl;
    display: flex; gap: 8px; flex-wrap: wrap;
    margin: 4px 0 10px;
}
.asp-step {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 14px; border-radius: 12px; font-size: .92rem; font-weight: 600;
    border: 1px solid rgba(148,163,184,.25);
    background: rgba(22,26,40,.6); color: #94A3B8;
}
.asp-step .n {
    display: inline-flex; align-items: center; justify-content: center;
    width: 22px; height: 22px; border-radius: 50%;
    background: rgba(148,163,184,.2); font-size: .8rem;
}
.asp-step.done {
    border-color: rgba(52,211,153,.5); color: #6EE7B7;
    background: rgba(6,78,59,.25);
}
.asp-step.done .n { background: rgba(52,211,153,.25); }
.asp-step.current {
    border-color: #8B5CF6; color: #E9D5FF;
    background: rgba(88,28,135,.3);
    box-shadow: 0 0 12px rgba(139,92,246,.35);
}
.asp-step.current .n { background: #8B5CF6; color: white; }
</style>
"""


def inject_theme() -> None:
    """Inject the global CSS. Call once, right after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_hero(user_email: str = "") -> None:
    email_line = f" · שלום <b>{user_email}</b>" if user_email else ""
    st.markdown(
        f"""
<div class="asp-hero">
  <h1>🎬 Ad Studio Pro</h1>
  <p>מהתמונה של המוצר ועד סרטון פרסומת מוכן — מחקר, תכנית, פרומטים, וידאו{email_line}</p>
  <div>
    <span class="asp-badge">Seedance 2.0</span>
    <span class="asp-badge">Seed Audio 1.0</span>
    <span class="asp-badge">עד 9 תמונות מוצר בסרטון אחד</span>
    <span class="asp-badge">רפרנס וידאו + אודיו</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_stepper(steps) -> None:
    """Pipeline progress pills.

    steps: list of (label, state) where state in {"done", "current", "todo"}.
    """
    items = []
    for i, (label, state) in enumerate(steps, 1):
        icon = "✓" if state == "done" else str(i)
        items.append(
            f'<div class="asp-step {state}"><span class="n">{icon}</span>{label}</div>'
        )
    st.markdown(f'<div class="asp-stepper">{"".join(items)}</div>', unsafe_allow_html=True)


def compute_full_pipeline_steps(ss) -> list:
    """Derive stepper states from st.session_state for the Full pipeline."""
    has_img = bool(ss.get("image_paths") or ss.get("image_path"))
    s1 = bool(ss.get("stage1"))
    s2 = bool(ss.get("stage2"))
    s3 = bool(ss.get("stage3"))
    s4 = bool(ss.get("stage4") or ss.get("video_results"))

    flags = [has_img, s1, s2, s3, s4]
    labels = ["העלאת מוצר", "מחקר", "תכנית", "פרומטים", "וידאו מוכן"]
    steps = []
    current_set = False
    for label, done in zip(labels, flags):
        if done:
            steps.append((label, "done"))
        elif not current_set:
            steps.append((label, "current"))
            current_set = True
        else:
            steps.append((label, "todo"))
    return steps
