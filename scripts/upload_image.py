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


import hashlib

_HOSTED_CACHE = {}   # sha1(bytes) -> public URL (cuts imgbb rate-limit hits)


def _prepare_for_upload(image_path: Path) -> bytes:
    """Normalize any image to a Seedance-safe JPEG:
      - RGB, JPEG q90, long side ≤ 2048px
      - short side ≥ 300px (Seedance minimum) — upscaled if needed
      - aspect ratio within 0.4–2.5 (Seedance limit) — padded with white if needed
    Raises a clear error if the file can't be decoded at all."""
    from io import BytesIO
    from PIL import Image
    try:
        img = Image.open(image_path)
        img.load()
    except Exception as e:
        raise RuntimeError(
            f"Can't read image '{Path(image_path).name}' ({e}). "
            "Re-save it as a regular JPG or PNG and upload again."
        )
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((2048, 2048))
    w, h = img.size
    if min(w, h) < 300:
        s = 320 / min(w, h)
        img = img.resize((int(w * s), int(h * s)), Image.LANCZOS)
        w, h = img.size
    ratio = w / h
    if ratio > 2.5 or ratio < 0.4:
        nw, nh = (w, int(w / 2.4)) if ratio > 2.5 else (int(h * 0.42), h)
        canvas = Image.new("RGB", (nw, nh), (255, 255, 255))
        canvas.paste(img, ((nw - w) // 2, (nh - h) // 2))
        img = canvas

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def to_data_url(data: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


def upload_to_imgbb(image_path: Path, data: bytes = None) -> str:
    """Upload to imgbb. Returns a public URL. Raises with imgbb's real reason."""
    key = _get("IMGBB_API_KEY")
    if not key:
        raise RuntimeError("IMGBB_API_KEY missing")
    data = data if data is not None else Path(image_path).read_bytes()
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
    return response.json()["data"]["url"]


def _upload_to_tmpfiles(name: str, data: bytes) -> str:
    r = requests.post("https://tmpfiles.org/api/v1/upload",
                      files={"file": (name, data, "image/jpeg")}, timeout=120)
    r.raise_for_status()
    raw = r.json().get("data", {}).get("url", "")
    if not raw:
        raise RuntimeError("tmpfiles: no url")
    return raw.replace("http://", "https://").replace("tmpfiles.org/", "tmpfiles.org/dl/")


def host_image_bytes(data: bytes, name: str = "image.jpg", log=print) -> str:
    """Put normalized JPEG bytes on a public host (imgbb → tmpfiles). Cached."""
    key = hashlib.sha1(data).hexdigest()
    if key in _HOSTED_CACHE:
        return _HOSTED_CACHE[key]
    errors = []
    for host, fn in (("imgbb", lambda: upload_to_imgbb(name, data)),
                     ("tmpfiles", lambda: _upload_to_tmpfiles(name, data))):
        try:
            url = fn()
            _HOSTED_CACHE[key] = url
            if errors:
                log(f"    ↪ hosted via {host} (earlier: {'; '.join(errors)})")
            return url
        except Exception as e:
            errors.append(f"{host}: {str(e)[:100]}")
    raise RuntimeError("All image hosts failed: " + "; ".join(errors))


def upload_image(image_path: Path, log=print) -> str:
    """Return an image reference Seedance can use.

    Primary: inline base64 data URL of a normalized JPEG — no third-party
    host involved (free hosts rate-limit, block cloud servers, or serve HTML
    pages to bots, which Seedance rejects as 'UnsupportedImageFormat').
    byteplus_client.submit_task() automatically re-hosts and retries if
    ModelArk ever refuses an inline image."""
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    return to_data_url(_prepare_for_upload(image_path))


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
