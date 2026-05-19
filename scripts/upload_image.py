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


def upload_to_imgbb(image_path: Path) -> str:
    """Upload to imgbb. Returns a public URL."""
    key = _get("IMGBB_API_KEY")
    if not key:
        raise RuntimeError(
            "IMGBB_API_KEY missing. Set it in .env locally OR in "
            "Streamlit Cloud Settings -> Secrets. "
            "Get a free key at https://api.imgbb.com/"
        )

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    response = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": key, "image": encoded},
        timeout=60,
    )
    response.raise_for_status()
    url = response.json()["data"]["url"]
    print(f"[OK] Uploaded {image_path.name} -> {url}")
    return url


def upload_image(image_path: Path) -> str:
    """
    Single entry point. Picks a backend based on what's configured.
    Future: auto-pick R2 if R2_* vars are set.
    """
    return upload_to_imgbb(image_path)


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
