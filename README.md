# Ad Studio Pro

Multi-product UGC video ad generator using **Claude.ai** (prompts) + **BytePlus Seedance 2.0** (video).

For ANY consumer product: rings, supplements, gadgets, food, apparel, beauty, jewelry, etc.

## Quick start

1. **`1_SETUP.bat`** / **`1_SETUP.command`** — installs packages (one time)
2. **`START_CHROME.bat`** / **`START_CHROME.command`** — opens Chrome with CDP (one time per session)
3. **`APP_START.bat`** / **`APP_START.command`** — opens the web app

In the app:
- Describe your ad in Hebrew or English
- Upload product images (up to 9)
- Set duration / aspect / quality
- Click **"צור פרומטים"** — Claude writes 1-3 variations
- Click **"צור וידאו"** — Seedance generates MP4

## How it differs from `thunderfit-ads`

`thunderfit-ads` is the original, working version locked to ring-specific rules.
`ad-studio-pro` is **product-agnostic** — works for any consumer product.

## Files

- `scripts/app.py` — Streamlit UI
- `scripts/prompt_generator.py` — Claude.ai via Chrome CDP, embeds arcads-prompts skill
- `scripts/byteplus_client.py` — Seedance 2.0 wrapper
- `scripts/upload_image.py` — imgbb
- `scripts/upload_video.py` — catbox.moe (for video references)
- `scripts/video_stitcher.py` — ffmpeg
- `.env` — API keys
- `prompts/` — saved ad prompts (empty until you save your own)
