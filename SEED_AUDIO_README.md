# 🎙 Seed Audio 1.0 — יצירת קול (voice) בתוך Ad Studio Pro

יצירת קטעי קול (קריינות, דיאלוג רב-דמויות, רגש, מוזיקת רקע ואפקטים) עם
**BytePlus Seed Audio 1.0**. את הקול שנוצר אפשר להוריד, או להזריק לסידנס 2.0
כ-`reference_audio`.

> חשוב: זה שירות **נפרד** מסידנס. סידנס רץ על ModelArk (`ARK_API_KEY`),
> ו-Seed Audio רץ על **קונסולת ה-Voice** של BytePlus עם **מפתח משלו**.

## הפעלה חד-פעמית (חובה)

1. היכנס לקונסולת ה-Voice: https://console.byteplus.com/voice/new/setting/activate?projectName=default
2. מצא את השירות **"Dola_SeedSpeech_Seed_Audio_V1"** ולחץ **Activate** (זמין מ-29 ביוני).
3. קח את ה-**API Key** (מסעיף *API Keys* בקונסולה).
4. הדבק אותו ב-`.env`:
   ```
   SEED_AUDIO_API_KEY=<המפתח מקונסולת ה-Voice>
   ```
   (זה ה-`X-Api-Key`. **לא** אותו מפתח כמו `ARK_API_KEY` של סידנס.)

## פרטי ה-API (מה-Integration Guide הרשמי)

| פריט | ערך |
|------|-----|
| Endpoint | `POST https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/create` |
| Content-Type | `application/json` |
| אימות | הדר `X-Api-Key` (מומלץ) · או legacy `X-Api-App-Id` + `X-Api-Access-Key` |
| סגנון | **סינכרוני** — POST אחד מחזיר את האודיו (base64 + `url` זמני ל-~2 שעות). אין polling. |
| טקסט | `text_prompt` עד 2,048 תווים |
| פלט | עד 120 שניות. פורמטים: wav/mp3/pcm/ogg_opus. Sample rate: 8/16/24/32/44.1/48kHz |
| בקרות | `speech_rate` & `loudness_rate` (מספר שלם −50…100; 0=רגיל, 100=×2, −50=×0.5) · `pitch_rate` (−12…12) |
| רפרנס | עד 3 אודיו (≤30s / ≤10MB) **או** תמונה אחת — לא מעורבב. בפרומט: @Audio1/@Audio2/@Audio3 |
| מחיר | ~0.15$ לדקת אודיו שנוצרת |

## מה נוסף לפרויקט

| קובץ | תפקיד |
|------|-------|
| `scripts/seed_audio_client.py` | הלקוח ל-API (סינכרוני, `X-Api-Key`, מפענח base64 לקובץ) |
| `scripts/generate_audio.py` | הרצה מהטרמינל (CLI) |
| `scripts/audio_studio.py` | מסך "🎙 מצב קול" ב-Streamlit (צ'קבוקס בראש האפליקציה) |
| `.env` / `.env.example` | `SEED_AUDIO_API_KEY`, `SEED_AUDIO_URL`, `SEED_AUDIO_MODEL_ID` |

## שימוש באפליקציה

1. מריצים כרגיל (`APP_START`).
2. בראש העמוד מסמנים **"🎙 מצב יצירת קול (Seed Audio 1.0)"**.
3. כותבים פרומט (תיאור סצנה/קול + הטקסט), בוחרים פורמט/מהירות/גובה, ואפשר להעלות רפרנס-אודיו.
4. **צור קול** → מנגן + הורדה. הקול מתפרסם ל-URL יציב (קטבוקס) ונשמר כרפרנס לסידנס.
5. מבטלים את הסימון כדי לחזור למסך הווידאו.

## שימוש מהטרמינל

```bash
# בדיקת חיבור מהירה
python scripts/seed_audio_client.py

# T2A — תיאור קול/סצנה + הטקסט להקראה
python scripts/generate_audio.py \
  "Warm female narrator, calm and confident: 'This ring tracks your sleep.'" \
  --name vo --format mp3

# שכפול קול מרפרנס (URL ציבורי), מסומן @Audio1 בטקסט
python scripts/generate_audio.py \
  "@Audio1 as the narrator: 'Welcome to the store.'" \
  --ref-audio https://your-bucket.com/voice.mp3 --name testimonial
```

## עברית — המצב הנוכחי

לפי הדוקומנטציה הרשמית, Seed Audio 1.0 תומך כרגע ב**אנגלית וסינית** בלבד,
**"more languages coming by the end of July"**. כלומר עברית עדיין לא נתמכת
רשמית. הקוד שולח עברית בכל זאת כדי לבדוק בפועל — אבל אם האיכות/המבטא לא טובים,
עדיף לכתוב באנגלית, או להשתמש ב-TTS ייעודי לעברית ואז להזריק את הקובץ לסידנס
כ-`reference_audio`. שווה לבדוק שוב בסוף יולי אם נוספה עברית.

## טיפים לפרומט טוב (מהמדריך הרשמי)

פרומט T2A טוב כולל: (1) תיאור סביבה/מזג-אוויר/מיקום, (2) מוזיקת רקע ואפקטים,
(3) פעולה/מראה של הדמות, (4) תיאור קול (מגדר/גיל/רגש/טון/מהירות), (5) מה
הדמות אומרת. לדיאלוג רב-דמויות — פשוט מתארים כל דובר בשורה שלו בתוך אותו פרומט.

## אם מקבלים שגיאה

- **שגיאת אימות/מפתח:** ודא ש-`SEED_AUDIO_API_KEY` הוא המפתח מקונסולת ה-Voice
  ושהשירות `Dola_SeedSpeech_Seed_Audio_V1` מופעל.
- **שגיאת voiceprint/clone/sensitive:** פשט את תיאור הקול, הימנע מהתייחסות
  לאנשים אמיתיים או לקולות מזוהים.
- **קול legacy:** אם אתה משתמש בקונסולה הישנה, הגדר `SEED_AUDIO_APP_ID` +
  `SEED_AUDIO_ACCESS_KEY` במקום `SEED_AUDIO_API_KEY`.
