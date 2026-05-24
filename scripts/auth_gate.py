"""
Auth gate — Custom Google OAuth flow with persistent URL token.

PERSISTENCE FIX (2026-05-24):
After OAuth succeeds we set ?t=<HMAC-signed token> in the URL. The token holds
the user's email + timestamp, signed with COOKIE_SECRET, valid for 30 days.
The browser keeps the URL through refreshes — so the user no longer has to
re-login on every reload. The token is stateless: any Streamlit Cloud replica
can verify it without shared storage.

Why custom (not st.login())?
Streamlit's built-in st.login() has a known MismatchingStateError bug on
Streamlit Cloud (multi-replica architecture loses the OAuth state cookie
between request initiation and callback). We bypass it by managing the
OAuth flow ourselves using HMAC-signed state + HMAC-signed auth token.

Rules:
- Anyone can click "Sign in with Google".
- After Google authentication, we verify the email ends in @neobrands.io.
- If yes → user is logged in for 30 days (URL token). If not → rejection.
- Users can log out anytime via the sidebar (clears URL token + session).

Setup (one time, in Google Cloud Console):
1. https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID → Web application
3. Authorized redirect URI: https://ad-studio-pro.streamlit.app/
4. Paste client_id / client_secret into Streamlit Secrets [auth.google].
"""

import base64
import hmac
import hashlib
import secrets
import time
from urllib.parse import urlencode

import requests
import streamlit as st

# Only these email domains can log in.
ALLOWED_DOMAINS = {"neobrands.io"}

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Auth token lifetime — 30 days.
TOKEN_MAX_AGE = 60 * 60 * 24 * 30


# ── Config readers ──────────────────────────────────────────


def _get_oauth_config():
    """Read OAuth config from Streamlit Secrets."""
    try:
        auth = st.secrets.get("auth", None)
    except Exception:
        return None
    if not auth:
        return None
    google = auth.get("google", None) or auth
    return {
        "client_id": google.get("client_id", "") or "",
        "client_secret": google.get("client_secret", "") or "",
        "redirect_uri": auth.get("redirect_uri", "") or "",
        "cookie_secret": auth.get("cookie_secret", "") or "fallback-secret-change-me",
    }


# ── Stateless HMAC-signed OAuth state (short-lived, 10min) ────────


def _make_signed_state(secret: str) -> str:
    """Create a signed state token: nonce.timestamp.signature."""
    nonce = secrets.token_urlsafe(16)
    ts = str(int(time.time()))
    payload = f"{nonce}.{ts}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{payload}.{sig}"


def _verify_signed_state(state: str, secret: str, max_age_seconds: int = 600) -> bool:
    """Verify a signed state token (OAuth CSRF state)."""
    try:
        parts = state.split(".")
        if len(parts) != 3:
            return False
        nonce, ts, sig = parts
        payload = f"{nonce}.{ts}"
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
        if not hmac.compare_digest(sig, expected):
            return False
        if time.time() - int(ts) > max_age_seconds:
            return False
        return True
    except Exception:
        return False


# ── Stateless HMAC-signed AUTH token (long-lived, 30 days) ────────


def _make_auth_token(email: str, secret: str) -> str:
    """Create a signed auth token: b64(email).timestamp.signature."""
    encoded_email = base64.urlsafe_b64encode(email.encode()).decode().rstrip("=")
    ts = str(int(time.time()))
    payload = f"{encoded_email}.{ts}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload}.{sig}"


def _verify_auth_token(token: str, secret: str):
    """Verify a signed auth token. Returns email str or None on failure."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        encoded_email, ts, sig = parts
        payload = f"{encoded_email}.{ts}"
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return None
        if time.time() - int(ts) > TOKEN_MAX_AGE:
            return None
        pad = "=" * (-len(encoded_email) % 4)
        email = base64.urlsafe_b64decode(encoded_email + pad).decode()
        return email
    except Exception:
        return None


def _auth_configured() -> bool:
    cfg = _get_oauth_config()
    if not cfg:
        return False
    return bool(cfg["client_id"]) and "REPLACE_WITH" not in cfg["client_id"]


def _domain_ok(email: str) -> bool:
    if "@" not in email:
        return False
    return email.split("@", 1)[1].lower() in ALLOWED_DOMAINS


# ── OAuth flow steps ────────────────────────────────────────


def _build_auth_url() -> str:
    """Build a Google OAuth URL with a freshly-signed state."""
    cfg = _get_oauth_config()
    state = _make_signed_state(cfg["cookie_secret"])
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
        "access_type": "online",
    }
    return GOOGLE_AUTH_URL + "?" + urlencode(params)


def _exchange_code_for_user(code: str):
    """Exchange OAuth code for user info. Returns (user_dict, error_str)."""
    cfg = _get_oauth_config()
    try:
        token_resp = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "redirect_uri": cfg["redirect_uri"],
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        token_data = token_resp.json()
        if "access_token" not in token_data:
            return None, f"Token exchange failed: {token_data.get('error_description', token_data)}"

        user_resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
            timeout=15,
        )
        user_info = user_resp.json()
        if "email" not in user_info:
            return None, f"User info missing email: {user_info}"
        return user_info, None
    except Exception as e:
        return None, f"OAuth error: {e}"


def _process_callback_if_present():
    """If URL has ?code=&state=, process it and set ?t=<auth-token>."""
    params = st.query_params
    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        return

    cfg = _get_oauth_config()

    # Verify HMAC on state — no shared storage needed.
    if not _verify_signed_state(state, cfg["cookie_secret"]):
        # Clear the code/state from URL, set error
        try:
            for k in ("code", "state", "scope", "authuser", "prompt", "hd"):
                if k in st.query_params:
                    del st.query_params[k]
        except Exception:
            pass
        st.session_state["_auth_error"] = (
            "פג תוקף או חתימה לא תקינה של ההתחברות. לחץ שוב על 'התחבר עם Google'."
        )
        return

    user_info, err = _exchange_code_for_user(code)

    # Clear the OAuth-specific query params no matter what
    try:
        for k in ("code", "state", "scope", "authuser", "prompt", "hd"):
            if k in st.query_params:
                del st.query_params[k]
    except Exception:
        pass

    if err or not user_info:
        st.session_state["_auth_error"] = err or "OAuth failed"
        return

    email = (user_info.get("email") or "").strip().lower()
    name = user_info.get("name") or email
    picture = user_info.get("picture") or ""

    # Issue a long-lived auth token in the URL — survives refresh.
    token = _make_auth_token(email, cfg["cookie_secret"])
    try:
        st.query_params["t"] = token
    except Exception:
        pass

    # Also keep session state for the immediate render.
    st.session_state["_auth_user"] = {
        "email": email,
        "name": name,
        "picture": picture,
    }


def _try_url_token() -> dict | None:
    """If ?t=<token> is in the URL and valid, return a user dict."""
    cfg = _get_oauth_config()
    if not cfg:
        return None
    token = st.query_params.get("t")
    if not token:
        return None
    email = _verify_auth_token(token, cfg["cookie_secret"])
    if not email:
        return None
    return {"email": email, "name": email, "picture": ""}


# ── Public API ──────────────────────────────────────────────


def require_login() -> dict:
    """Returns the authorized user dict, or renders gate + st.stop()."""
    if not _auth_configured():
        _render_setup_needed()
        st.stop()

    # 1. URL token wins — survives refreshes + replica swaps.
    user = _try_url_token()
    if user:
        if not _domain_ok(user["email"]):
            _render_rejection(user["email"])
            st.stop()
        # Mirror to session for downstream code
        st.session_state["_auth_user"] = user
        return user

    # 2. OAuth callback (just returned from Google).
    _process_callback_if_present()

    # 3. Session state (post-callback render).
    user = st.session_state.get("_auth_user")
    if user:
        if not _domain_ok(user["email"]):
            _render_rejection(user["email"])
            st.stop()
        return user

    # 4. Nothing → show landing.
    _render_landing()
    st.stop()


def render_logout_button():
    user = st.session_state.get("_auth_user")
    if not user:
        # Check URL token in case session got cleared but token still valid
        url_user = _try_url_token()
        if not url_user:
            return
        user = url_user
    with st.sidebar:
        st.markdown("---")
        st.caption(f"\U0001F464 {user['email']}")
        if st.button("התנתק", use_container_width=True):
            st.session_state.pop("_auth_user", None)
            st.session_state.pop("_oauth_state", None)
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.rerun()


# ── UI screens ──────────────────────────────────────────────


def _render_landing():
    st.set_page_config(page_title="Ad Studio Pro — Sign in",
                       page_icon="🎬", layout="centered")
    st.title("🎬 Ad Studio Pro")
    st.write("")
    st.markdown("### ברוך הבא לסטודיו של **neobrands.io**")
    st.write("")
    st.info(
        "מערכת זו פתוחה אך ורק לעובדי **neobrands.io**.\n\n"
        "התחבר עם חשבון Google בעל מייל `@neobrands.io` כדי להתחיל."
    )
    err = st.session_state.pop("_auth_error", None)
    if err:
        st.warning(err)
    st.write("")
    auth_url = _build_auth_url()
    st.link_button("🔐 התחבר עם Google", auth_url,
                   type="primary", use_container_width=True)
    st.write("")
    st.caption("אם אין לך עדיין מייל `@neobrands.io` — פנה למנהל החברה.")
    st.caption("💡 לאחר התחברות ראשונית, תישאר מחובר ל-30 ימים.")


def _render_rejection(email: str):
    st.set_page_config(page_title="Ad Studio Pro — Access denied",
                       page_icon="🚫", layout="centered")
    st.title("🚫 גישה לא מאושרת")
    st.error(
        f"המייל **{email}** אינו של עובד neobrands.io.\n\n"
        "המערכת פתוחה אך ורק לכתובות שמסתיימות ב-`@neobrands.io`."
    )
    st.write("")
    if st.button("🔄 נסה עם חשבון אחר", use_container_width=True):
        st.session_state.pop("_auth_user", None)
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()


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
    st.write("2. הוסף redirect URI: `https://ad-studio-pro.streamlit.app/`")
    st.write("3. הדבק את ה-`[auth]` block ב-Streamlit Cloud → Settings → Secrets")
    st.write("4. רענן את הדף")
