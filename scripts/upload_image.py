"""
Upload local images to a public URL so BytePlus ModelArk can fetch them.

Default backend: imgbb (free, simple).  Get a key at https://api.imgbb.com/

Production tip: replace with Cloudflare R2 or AWS S3 — see upload_to_r2()
stub at the bottom of this file.
"""

import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Streamlit Cloud fallback.
try:
    import streamlit as st
    _SECRETS = dict(st.secrets) if hasattr(st, "secrets") else {}
except Exception:
    _SECRETS = {}


def _get(key, default=""):
    val = os.getenv(key)
    if val:
        return val
    return _SECRETS.get(key, default)


IMGBB_API_KEY = _get("IMGBB_API_KEY")


def _prepare_for_upload(image_path: Path) -> bytes:
    """Normalize any image to a clean JPEG ≤2048px on the long side (~<5MB).
    Fixes imgbb 400s from oversized / oddly-encoded files (e.g. JPEG data saved
    with a .png name, huge phone photos, RGBA/CMYK)."""
    from io import BytesIO
    from PIL import Image
    img = Image.open(image_path)
    img.load()
    if img.mode not in ("RGB", "L"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA"):
            bg.paste(img, mask=img.split()[-1])
        else:
            bg.paste(img.convert("RGB"))
        img = bg
    elif img.mode == "L":
        img = img.convert("RGB")
    img.thumbnail((2048, 2048))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def upload_to_imgbb(image_path: Path, data: bytes = None) -> str:
    """Upload to imgbb. Returns a public URL. Raises with imgbb's real reason."""
    key = _get("IMGBB_API_KEY")
    if not key:
        raise RuntimeError("IMGBB_API_KEY missing (Streamlit Secrets / .env).")
    image_path = Path(image_path)
    data = data if data is not None else image_path.read_bytes()
    response = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": key, "image": base64.b64encode(data).decode()},
        timeout=60,
    )
    if response.status_code >= 400:
        reason = response.text[:300]
        try:
            reason = response.json().get("error", {}).get("message", reason)
        except Exception:
            pass
        raise RuntimeError(f"imgbb {response.status_code}: {reason}")
    url = response.json()["data"]["url"]
    print(f"[OK] imgbb {image_path.name} -> {url}")
    return url


def _upload_to_catbox(name: str, data: bytes) -> str:
    r = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": (name, data, "image/jpeg")},
        timeout=120,
    )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"catbox unexpected: {url[:120]}")
    return url


def _upload_to_tmpfiles(name: str, data: bytes) -> str:
    r = requests.post(
        "https://tmpfiles.org/api/v1/upload",
        files={"file": (name, data, "image/jpeg")},
        timeout=120,
    )
    r.raise_for_status()
    raw = r.json().get("data", {}).get("url", "")
    if not raw:
        raise RuntimeError("tmpfiles: no url")
    return raw.replace("tmpfiles.org/", "tmpfiles.org/dl/")


def upload_image(image_path: Path, log=print) -> str:
    """Public URL for an image, with fallbacks so one host can't block generation.
    Order: imgbb → catbox → tmpfiles → inline base64 data URL (accepted by
    ModelArk for reference images)."""
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    try:
        data = _prepare_for_upload(image_path)
    except Exception:
        data = image_path.read_bytes()
    safe_name = "img_" + "".join(c if c.isalnum() else "_" for c in image_path.stem)[:40] + ".jpg"

    errors = []
    for host, fn in (("imgbb", lambda: upload_to_imgbb(image_path, data)),
                     ("catbox", lambda: _upload_to_catbox(safe_name, data)),
                     ("tmpfiles", lambda: _upload_to_tmpfiles(safe_name, data))):
        try:
            url = fn()
            if errors:
                log(f"    ↪ uploaded via {host} (earlier: {'; '.join(errors)})")
            return url
        except Exception as e:
            errors.append(f"{host}: {str(e)[:120]}")

    # Last resort: inline data URL (no external host needed)
    log(f"    ↪ all image hosts failed ({'; '.join(errors)}) — sending image inline")
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


# ---------------------------------------------------------------------------
# Production stub: Cloudflare R2 (boto3 S3-compatible). Uncomment + install
# `boto3` to use.
# ---------------------------------------------------------------------------
# def upload_to_r2(image_path: Path) -> str:
#     import boto3
#     account_id = os.environ["R2_ACCOUNT_ID"]
#     bucket = os.environ["R2_BUCKET"]
#     s3 = boto3.client(
#         "s3",
#         endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
#         aws_access_key_id=os.environ["R2_ACCESS_KEY"],
#         aws_secret_access_key=os.environ["R2_SECRET_KEY"],
#     )
#     key = f"thunderfit/{image_path.name}"
#     s3.upload_file(str(image_path), bucket, key, ExtraArgs={"ACL": "public-read"})
#     return f"https://{bucket}.r2.dev/{key}"
