# Google OAuth Setup — One Time, ~5 Minutes

This wires up Google Sign-In for `https://ad-studio-pro.streamlit.app/`
so only people with an `@neobrands.io` email can log in.

You do this ONCE. After that any new neobrands.io employee can sign in instantly.

---

## Step 1 — Create a Google OAuth Client

1. Open https://console.cloud.google.com/apis/credentials
2. If you don't have a project yet:
   - Top bar → **Select a project** → **New Project**
   - Name it `ad-studio-pro` → **Create**
3. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
4. If it asks you to configure the consent screen first:
   - **User Type:** External
   - **App name:** Ad Studio Pro
   - **User support email:** your email
   - **Developer contact email:** your email
   - Save and continue through the screens (you can skip scopes & test users)
   - Back on the OAuth client page, click **+ CREATE CREDENTIALS** → **OAuth client ID** again
5. **Application type:** Web application
6. **Name:** Ad Studio Pro Web
7. **Authorized redirect URIs:** click **+ ADD URI** and paste:

   ```
   https://ad-studio-pro.streamlit.app/oauth2callback
   ```

8. Click **CREATE**
9. A dialog appears with your **Client ID** and **Client Secret** — keep this tab open, you'll copy these in Step 3.

---

## Step 2 — Generate a Cookie Secret

The cookie secret is used to sign the session cookie. Generate one:

**On Windows (cmd or PowerShell):**

```cmd
python -c "import secrets; print(secrets.token_hex(32))"
```

You'll get a 64-character hex string. Copy it.

---

## Step 3 — Paste Into Streamlit Cloud Secrets

1. Open https://share.streamlit.io/
2. Find `ad-studio-pro` → click the `⋮` menu → **Settings** → **Secrets**
3. Find the `[auth]` block at the bottom and replace the placeholder lines:

   ```toml
   [auth]
   redirect_uri = "https://ad-studio-pro.streamlit.app/oauth2callback"
   cookie_secret = "<the 64-hex string from Step 2>"
   client_id = "<the Client ID from Step 1>"
   client_secret = "<the Client Secret from Step 1>"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```

4. Click **Save changes**
5. Streamlit Cloud will rebuild in ~30 seconds

---

## Step 4 — Test

1. Open https://ad-studio-pro.streamlit.app/ in an incognito window
2. You should see a landing page with a **"🔐 התחבר עם Google"** button
3. Click it → Google OAuth flow
4. Sign in with your `@neobrands.io` Google account → you're in
5. Try signing in with a personal Gmail (`@gmail.com`) → you should be rejected with a polite message

---

## Adding more domains (if neobrands.io gets a parent brand later)

Edit `scripts/auth_gate.py`:

```python
ALLOWED_DOMAINS = {"neobrands.io", "neobrands.com"}
```

Push to GitHub — done.

---

## Troubleshooting

**"redirect_uri_mismatch"** when clicking Sign in with Google:
You forgot to add `https://ad-studio-pro.streamlit.app/oauth2callback` to the Google
OAuth client's Authorized redirect URIs in Step 1.7. Add it and try again.

**"This app is blocked"** with a 403 page:
The Google OAuth consent screen is in "Testing" mode and your email isn't on the
test users list. Either:
- Add your email under OAuth consent screen → Test users, OR
- Publish the app (OAuth consent screen → PUBLISH APP) — this lets any
  Google account sign in (still gated by the `@neobrands.io` check in the code).
