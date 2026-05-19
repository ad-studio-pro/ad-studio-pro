"""
Auth gate — Google OAuth via Streamlit's native st.login() / st.user.

Rules:
- Anyone can click "Sign in with Google" on the landing screen.
- After Google authentication, we verify the email ends in @neobrands.io.
- If the domain matches → user is allowed in (a session is established).
- If the domain does NOT match → user is shown a polite rejection.
- Users can log out at any time via the sidebar.

Setup (one time, in Google Cloud Console):
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID → Web application
3. Authorized redirect URI:
     https://ad-studio-pro.streamlit.app/oauth2callback
4. Copy the Client ID + Client Secret into Streamlit Secrets:
     [auth]
     redirect_uri = "https://ad-studio-pro.streamlit.app/oauth2callback"
     cookie_secret = "<run: python -c 'import secrets;print(secrets.token_hex(32))'>"
     client_id = "..."
     client_secret = "..."
     server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
"""

import streamlit as st

# Only these email domains can log in.
ALLOWED_DOMAINS = {"neobrands.io"}


def _user_email() -> str:
    """Read the logged-in user's email if any, else empty string."""
    try:
        user = getattr(st, "user", None)
        if user is None:
            return ""
        if not getattr(user, "is_logged_in", False):
            return ""
        return (getattr(user, "email", "") or "").strip().lower()
    except Exception:
        return ""


def _domain_ok(email: str) -> bool:
    if "@" not in email:
        return False
    return email.split("@", 1)[1] in ALLOWED_DOMAINS


def _auth_configured() -> bool:
    """Check whether the [auth] block is present in Streamlit Secrets."""
    try:
        auth = st.secrets.get("auth", None)
        if not auth:
            return False
        cid = auth.get("client_id", "")
        return bool(cid) and "REPLACE_WITH" not in cid
    except Exception:
        return False


def require_login() -> dict:
    """
    Call at the very top of app.py. Returns the verified user dict.
    If not logged in OR domain-blocked, renders the gate UI and calls
    st.stop() so the rest of the page does NOT render.
    """
    # If [auth] block isn't filled in yet — show a setup-needed screen
    # instead of crashing on st.login("google").
    if not _auth_configured():
        _render_setup_needed()
        st.stop()

    email = _user_email()

    # Not logged in → show landing page
    if not email:
        _render_landing()
        st.stop()

    # Logged in but wrong domain → block
    if not _domain_ok(email):
        _render_rejection(email)
        st.stop()

    # Approved
    return {
        "email": email,
        "name": getattr(st.user, "name", "") or email,
        "picture": getattr(st.user, "picture", "") or "",
    }


def _render_setup_needed():
    st.set_page_config(page_title="Ad Studio Pro — Setup needed",
                       page_icon="🔧", layout="centered")
    st.title("🔧 הגדרת Google OAuth")
    st.warning(
        "ה-`[auth]` block ב-Streamlit Secrets עדיין לא הוגדר. "
        "האפליקציה תתחיל לעבוד ברגע שתשלים את הצעדים בקובץ "
        "`GOOGLE_OAUTH_SETUP.md`."
    )
    st.markdown("---")
    st.write("**הצעדים בקצרה:**")
    st.write("1. צור OAuth Client ב-https://console.cloud.google.com/apis/credentials")
    st.write("2. הוסף redirect URI: `https://ad-studio-pro.streamlit.app/oauth2callback`")
    st.write("3. הדבק את ה-`[auth]` block ב-Streamlit Cloud → Settings → Secrets")
    st.write("4. רענן את הדף")


def render_logout_button():
    """Render a small logout control in the sidebar."""
    email = _user_email()
    if not email:
        return
    with st.sidebar:
        st.markdown("---")
        st.caption(f"👤 {email}")
        if st.button("התנתק", use_container_width=True):
            st.logout()


def _render_landing():
    st.set_page_config(page_title="Ad Studio Pro — Sign in",
                       page_icon="🎬", layout="centered")
    st.title("🎬 Ad Studio Pro")
    st.write("")
    st.markdown(
        "### ברוך הבא לסטודיו של **neobrands.io**"
    )
    st.write("")
    st.info(
        "מערכת זו פתוחה אך ורק לעובדי **neobrands.io**.\n\n"
        "התחבר עם חשבון Google בעל מייל `@neobrands.io` כדי להתחיל."
    )
    st.write("")
    if st.button("🔐 התחבר עם Google", type="primary", use_container_width=True):
        st.login("google")
    st.write("")
    st.caption(
        "אם אין לך עדיין מייל `@neobrands.io` — פנה למנהל החברה."
    )


def _render_rejection(email: str):
    st.set_page_config(page_title="Ad Studio Pro — Access denied",
                       page_icon="🚫", layout="centered")
    st.title("🚫 גישה לא מאושרת")
    st.error(
        f"המייל **{email}** אינו של עובד neobrands.io.\n\n"
        "המערכת פתוחה אך ורק לכתובות שמסתיימות ב-`@neobrands.io`."
    )
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 נסה עם חשבון אחר", use_container_width=True):
            st.logout()
    with col2:
        st.write("")  # spacer
