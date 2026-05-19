# 🚀 Streamlit Cloud Deploy Guide

מטרה: להעלות את ad-studio-pro לכתובת אונליין שעובדי החברה יוכלו להיכנס אליה.

**יעד:** משהו כמו `https://ad-studio-pro-roi.streamlit.app/`

---

## 🎯 דרישות מקדימות (פעם אחת)

| מה | למה | זמן |
|---|---|---|
| חשבון GitHub | מקור הקוד | 2 דק׳ |
| חשבון Streamlit Cloud | hosting (חינם) | 1 דק׳ |
| Anthropic API key | במקום Chrome CDP | 5 דק׳ |
| כל יתר המפתחות | כבר יש לך (BytePlus, imgbb, Gemini, Tavily) | ✓ |

---

## שלב 1 — מפתח Anthropic API

1. כנס ל-https://console.anthropic.com/
2. Sign up עם המייל שלך (אם אין)
3. Settings → **API Keys** → **Create Key**
4. שמור את המפתח (`sk-ant-api03-...`)
5. עלות: ~$0.02 לפרומט (כ-$50/חודש לקמפיין סביר)

---

## שלב 2 — העלאת הקוד ל-GitHub

```bash
cd C:\Users\PC\Documents\ad-studio-pro

# התקן git אם אין:  https://git-scm.com/download/win
git init
git add .
git commit -m "Initial commit"

# צור repo חדש (פרטי!) ב-https://github.com/new
# שם: ad-studio-pro
# Visibility: Private (חשוב — יש לך מפתחות!)

git remote add origin https://github.com/<your-username>/ad-studio-pro.git
git branch -M main
git push -u origin main
```

⚠️ **חשוב:** צריך לוודא ש-`.env` ו-`auth_config.yaml` הם ב-`.gitignore` (לא לעלות מפתחות!)

```
# .gitignore (כבר קיים בפרויקט):
.env
auth_config.yaml
venv/
__pycache__/
outputs/videos/*.mp4
outputs/logs/*.json
```

---

## שלב 3 — Streamlit Cloud

1. כנס ל-https://share.streamlit.io/
2. Sign in with GitHub
3. **New app** → **From existing repo**
4. בחר את ה-repo `ad-studio-pro`
5. **Main file path:** `scripts/app.py`
6. **App URL:** בחר slug (כמו `ad-studio-pro-roi`)
7. **Advanced settings → Secrets** — הדבק את כל המפתחות (ראה שלב 4)

לחץ Deploy.

---

## שלב 4 — Secrets (במקום .env)

ב-Streamlit Cloud → **Settings** → **Secrets** הדבק:

```toml
ARK_API_KEY = "ark-REPLACE-WITH-YOUR-KEY-FROM-byteplus-console"
ARK_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"
SEEDANCE_MODEL_ID = "dreamina-seedance-2-0-260128"

ANTHROPIC_API_KEY = "sk-ant-api03-..."  # ← המפתח החדש משלב 1
ANTHROPIC_MODEL = "claude-opus-4-6"

GEMINI_API_KEY = "AIzaSy-REPLACE-WITH-YOUR-KEY-FROM-aistudio.google.com"
TAVILY_API_KEY = "tvly-dev-REPLACE-WITH-YOUR-KEY-FROM-tavily.com"
SCRAPECREATORS_API_KEY = "REPLACE-WITH-YOUR-KEY-FROM-scrapecreators.com"
IMGBB_API_KEY = "REPLACE-WITH-YOUR-KEY-FROM-api.imgbb.com"

LLM_BACKEND = "api"  # ← חשוב: מכריח שימוש ב-API ולא ב-Chrome (אין Chrome בענן)
```

לחץ **Save**. האפליקציה תעלה מחדש אוטומטית.

---

## שלב 5 — הגדרת Auth (יוזרים)

### 5א. צור hash של סיסמה עבור כל יוזר

מקומית, פתח Terminal/CMD:
```bash
cd C:\Users\PC\Documents\ad-studio-pro
pip install streamlit-authenticator
python scripts/auth_make_hash.py "RoiPassword2026!"
```

תקבל hash שמתחיל ב-`$2b$12$...`. שמור אותו.

חזור על זה עבור כל עובד.

### 5ב. צור `auth_config.yaml` (מקומית, לא ב-git)

העתק את `auth_config.yaml.example` ל-`auth_config.yaml` ומלא:

```yaml
credentials:
  usernames:
    roi:
      email: agent1@romarketinggroup.com
      name: Roi Cohen
      password: $2b$12$AbCdEf...  # המ-hash משלב 5א
      role: admin
    daniel:
      email: daniel@romarketinggroup.com
      name: Daniel
      password: $2b$12$XyZ123...
      role: creator

cookie:
  expiry_days: 30
  key: "a-random-32-character-string-for-cookies-here"
  name: ad_studio_pro_auth
```

### 5ג. העלה את `auth_config.yaml` ל-Streamlit Cloud

⚠️ **לא** לדחוף ל-git. במקום:
- Streamlit Cloud → **Settings** → **Secrets** → הוסף הסעיף הזה:

```toml
[auth]
config_yaml = """
credentials:
  usernames:
    roi:
      email: agent1@romarketinggroup.com
      name: Roi Cohen
      password: $2b$12$AbCdEf...
      role: admin
    daniel:
      ...
cookie:
  expiry_days: 30
  key: "a-random-32-character-string"
  name: ad_studio_pro_auth
"""
```

ועדכן את הקוד שיקרא מ-`st.secrets["auth"]["config_yaml"]` במקום מקובץ.

---

## שלב 6 — בדיקה

1. כנס ל-`https://ad-studio-pro-roi.streamlit.app/`
2. אמור להופיע מסך login
3. הזן `roi` + הסיסמה
4. תכנס לאפליקציה — Sidebar אמור להראות:
   - ✅ Anthropic API (LLM_BACKEND=api)
   - ✅ Gemini Vision
   - ✅ Tavily, imgbb, ffmpeg
5. תעלה תמונה, תרוץ Stage 1 — אמור לעבוד **בלי Chrome**!

---

## עלויות חודשיות מוערכות

| שירות | עלות | הערה |
|---|---|---|
| Streamlit Cloud | $0 | Free tier — עד 1GB RAM, public app (אבל יש auth!) |
| Anthropic API | ~$30-100 | תלוי בכמות פרומטים |
| BytePlus Seedance | ~$50-300 | תלוי בכמות וידאו (~$0.20-1 לוידאו) |
| imgbb | $0 | חינם |
| Tavily | $0 | חינם עד 1000 חיפושים/חודש |
| Gemini | $0 | Free tier — Vision API |
| **סה"כ** | **~$80-400** | תלוי בשימוש |

---

## בעיות נפוצות

| שגיאה | פתרון |
|---|---|
| "ANTHROPIC_API_KEY missing" | הוסף ב-Streamlit Secrets, ודא `LLM_BACKEND=api` |
| Login שגוי | בדוק שה-hash בקובץ תואם לסיסמה (תיצור מחדש עם auth_make_hash.py) |
| "Chrome CDP not running" | אסור — בענן אין Chrome. ודא `LLM_BACKEND=api` ב-secrets |
| Streamlit לא טוען | בדוק ש-`scripts/app.py` הוא Main file. בדוק את Logs |

---

## שלבי המשך (אחרי שעובד)

1. **דומיין מותאם:** `app.romarketinggroup.com` — דרך Cloudflare DNS → Streamlit URL
2. **UI מקצועי יותר:** מעבר ל-Next.js (שלב 2 בתוכנית הראשית)
3. **Database:** מעבר מקבצים מקומיים ל-Supabase Postgres
4. **Async jobs:** Inngest / Trigger.dev — שמשתמש לא ממתין

---

## עזרה

תקוע? קח צילום מסך של ה-Logs ב-Streamlit Cloud ושלח אלי.
