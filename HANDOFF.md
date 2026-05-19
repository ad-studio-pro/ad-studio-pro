# 🎁 Ad Studio Pro — Handoff Package

מערכת ליצירת פרסומות וידאו אוטומטית לכל מוצר:
**בריף → Claude כותב פרומטים → Seedance 2.0 מייצר וידאו**

הפרומטים נכתבים על ידי Claude שלך (Opus 4.7) דרך Chrome —
משתמש במנוי Claude שלך, **בלי תשלום API נוסף**.

---

## דרישות חובה (פעם אחת)

עובד על **Windows + Mac**:
- Windows: השתמש בקבצי `.bat` (1_SETUP.bat, START_CHROME.bat וכו')
- Mac: השתמש בקבצי `.command` (1_SETUP.command, START_CHROME.command וכו')

| מה | למה |
|---|---|
| Windows 10/11 *או* macOS | מערכת הפעלה |
| Python 3.10+ | להרצת הקוד. Windows: https://www.python.org/downloads/ (סמן "Add Python to PATH"). Mac: כבר מובנה ב-3.9; אפשר לשדרג עם `brew install python` |
| Google Chrome | האפליקציה מתחברת ל-Chrome |
| חשבון Claude.ai | Pro/Max עדיף (Opus 4.7) |
| מפתחות API | BytePlus + imgbb — **כבר מוגדרים ב-.env** |

---

## ⚡ סדר הקליקים (4 קליקים בלבד)

הקבצים זהים בתוכן בין Windows ו-Mac, רק שמם משתנה (`.bat` ↔ `.command`):

| מטרה | Windows | Mac |
|---|---|---|
| התקנה | `1_SETUP.bat` | `1_SETUP.command` |
| Chrome | `START_CHROME.bat` | `START_CHROME.command` |
| אפליקציה | `APP_START.bat` | `APP_START.command` |
| אבחון | `CHECK_CHROME.bat` | `CHECK_CHROME.command` |

### קליק 1 — התקנה (פעם אחת לחיים)
**`1_SETUP.bat`** (Windows) או **`1_SETUP.command`** (Mac) — מתקין Python packages: requests, dotenv, pillow, streamlit, playwright, imageio-ffmpeg. לוקח 1-2 דקות.

📌 **Mac note:** בפעם הראשונה Mac עשוי להתריע "Cannot be opened because it's from an unidentified developer". פתרון: קליק ימני על הקובץ → **Open** → אישור.

### קליק 2 — Chrome (פעם אחת בכל הדלקת מחשב)
**`START_CHROME.bat`** / **`START_CHROME.command`** — פותח Chrome עם CDP על פורט 9224.
- בפעם הראשונה: התחבר ל-claude.ai, בחר מודל **Opus 4.7** (לא Adaptive)
- השאר את החלון פתוח ברקע

### קליק 3 — האפליקציה
**`APP_START.bat`** / **`APP_START.command`** — פותח את האפליקציה בדפדפן.
ב-sidebar אמור להופיע 3 פעמים ✅:
- ✅ Claude.ai (Chrome on port 9224)
- ✅ imgbb (image hosting)
- ✅ ffmpeg

### קליק 4 — תייצר!
1. **כותב בריף** (עברית או אנגלית): מי האדם, איפה, מה ההוק, מה הטון
2. **מעלה תמונת/ות הטבעת** (עד 9)
3. בוחר **משך + יחס + איכות** (ברירת מחדל: 15s · 9:16 · 720p)
4. **"צור פרומטים"** — Claude יכתוב 1-3 גרסאות שונות
5. בוחר גרסה (או "**צור וידאו לכל הגרסאות**" - מאסטר), לוחץ **"צור וידאו"**

הוידאו יישמר ב: `outputs/videos/`

---

## ✨ תכונות מיוחדות

### וידאו ארוך (20-30 שניות)
מערכת **stitching אוטומטית**:
1. Claude כותב פתיחה של 15s שנגמרת במשפט שלם + ביט שקט
2. Seedance מייצר Video A
3. ffmpeg מחלץ את הפריים האחרון
4. Catbox.moe מארח את Video A
5. Claude מקבל את Video A + תמונת הטבעת ← כותב פרומט המשך
6. Seedance מייצר Video B (עם Video A כ-`reference_video`)
7. ffmpeg מדביק → MP4 אחד של 30 שניות

### גיוון אוטומטי
כל פעם שמייצרים פרומטים, Claude **חייב** לגוון:
- אתניות (Caucasian-American / Hispanic / Asian / African-American / Mixed)
- גיל (mid-20s עד early-40s)
- שיער / סטייל / מיקום בארה"ב

### כללי איכות מובנים
- ❌ אסור: shine, sheen, oily, sweaty, freckles across face, wedding ring, metal band
- ✅ Image 1 = הטבעת על יד שמאל בלבד, יד ימין ריקה
- ✅ אמריקאים בלבד עם מבטא אמריקאי

---

## פתרון בעיות

| שגיאה | פתרון |
|---|---|
| ❌ Chrome CDP not running on port 9224 | הפעל **`START_CHROME.bat`**. אם נכשל — סגור כל Chrome ב-Task Manager ונסה שוב. |
| ❌ ffmpeg חסר | הרץ **`1_SETUP.bat`** שוב |
| ❌ WinError 2 | אותו פתרון — חסר ffmpeg |
| ❌ "No module named streamlit" | הרץ **`1_SETUP.bat`** שוב |
| המפתח BytePlus לא תקף | פתח `.env` ב-Notepad, החלף את `ARK_API_KEY=` |
| הטבעת קופצת בין ידיים בוידאו | הפרומט אמור לכלול "LEFT hand" בכל ביט. אם לא, ערוך ידנית |

---

## API Keys (כלולים ב-.env)

הקובץ `.env` כולל:
- **`ARK_API_KEY`** — BytePlus ModelArk (חיוב לפי שימוש)
- **`IMGBB_API_KEY`** — אחסון תמונות (חינם)
- **`CDP_PORT=9224`** — פורט Chrome

⚠ **שימוש ב-API key שלי = חיוב על החשבון שלי**. אם אתה רוצה לעבוד עם המפתחות שלך:
1. פתח את `.env` ב-Notepad
2. החלף את `ARK_API_KEY=...` שלך (https://console.byteplus.com)
3. החלף את `IMGBB_API_KEY=...` שלך (https://api.imgbb.com/, חינם)
4. שמור

---

## כלי בדיקה

| Bat | מטרה |
|---|---|
| `2_TEST_API.bat` | בודק חיבור ל-BytePlus (בקשה זולה של 5 שניות) |
| `3_TEST_FULL.bat` | מייצר וידאו דמו של BytePlus (תה תפוחים) — בודק כל הצינור |
| `CHECK_CHROME.bat` | אבחון Chrome CDP — אם משהו לא מתחבר |
| `4_GENERATE_AD_chef.bat` | מייצר פרסומת מוכנה (chef, ללא האפליקציה) |
| `5_GENERATE_ALL_4.bat` | מייצר את 4 הפרסומות המוכנות ברצף |

---

## מבנה הפרויקט

```
thunderfit-ads/
├── 1_SETUP.bat                    ← התקנה
├── START_CHROME.bat               ← Chrome עם CDP
├── APP_START.bat                  ← האפליקציה  
├── CHECK_CHROME.bat               ← אבחון
├── EXPORT.bat / EXPORT_NO_KEYS.bat← להעביר למישהו אחר
│
├── .env                           ← API keys (פרטי!)
├── .env.example                   ← תבנית
├── requirements.txt
├── README.md
├── HANDOFF.md                     ← הקובץ הזה
├── קרא_אותי_קודם.txt
│
├── scripts/
│   ├── app.py                     ← Streamlit UI
│   ├── prompt_generator.py        ← Claude.ai דרך Playwright/CDP
│   ├── byteplus_client.py         ← BytePlus API
│   ├── upload_image.py            ← imgbb
│   ├── upload_video.py            ← catbox.moe (לוידאו references)
│   ├── video_stitcher.py          ← ffmpeg: extract + concat
│   ├── generate.py                ← CLI generator
│   ├── batch.py                   ← batch לפרסומות מוכנות
│   ├── test_connection.py
│   └── test_full_pipeline.py
│
├── prompts/                       ← פרסומות מוכנות (chef, crossfit, nurse, mother)
├── assets/product/                ← תמונות הטבעות
└── outputs/
    ├── videos/                    ← MP4 שיורדים
    └── logs/                      ← JSON לוגים
```

---

## עזרה

משהו לא עובד?
1. צילום מסך של החלון השחור / האפליקציה
2. שלח לי / לאדם שנתן לך את הזיפ
