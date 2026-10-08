"""
ModelArk private asset library (Virtual Portrait / Real-human) — AK/SK client.

Lets the app upload our OWN AI characters to the Virtual Portrait library
(group type "AIGC"), list them, and delete them — then use them in Seedance
as asset://<id>. Also lists the verified Real-human assets ("LivenessFace").

Auth: BytePlus OpenAPI V4 (HMAC-SHA256) with an IAM Access Key / Secret Key —
NOT the ARK API key. Secrets (Streamlit Secrets or .env):
    BYTEPLUS_ACCESS_KEY   (AKLT...)
    BYTEPLUS_SECRET_KEY
    BYTEPLUS_SESSION_TOKEN  (only for temporary AKTP... keys)
    ASSET_PROJECT_NAME      (default "default")

Signing follows the official BytePlus SA implementation
(github.com/byteplus-sa/ark-mcp, MIT) — host ark.ap-southeast-1.byteplusapi.com,
service "ark", Version 2024-01-01.

Free "Entry" plan limits: 50 assets + 50 groups, CreateAsset ≤ 3/minute.
CreateAsset needs a publicly reachable HTTPS image URL and is asynchronous —
poll GetAsset until Status is Active (usable) or Failed.
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests

HOST = "ark.ap-southeast-1.byteplusapi.com"
REGION = "ap-southeast-1"
SERVICE = "ark"
VERSION = "2024-01-01"
CREATE_ASSET_MIN_INTERVAL = 21.0   # Entry plan: 3 CreateAsset calls per minute
FREE_PLAN_LIMIT = 50

def _flat_secrets() -> dict:
    """Read Streamlit Secrets LIVE (not cached at import), flattening any
    [sections] and matching names case-insensitively."""
    out = {}
    try:
        import streamlit as st
        def walk(d):
            for k, v in dict(d).items():
                if hasattr(v, "items"):
                    walk(v)
                else:
                    out.setdefault(str(k).strip().upper(), v)
        walk(st.secrets)
    except Exception:
        pass
    return out


def _get(*keys, default=""):
    sec = _flat_secrets()
    for k in keys:
        v = os.getenv(k) or sec.get(k.upper())
        if v:
            return str(v).strip().strip('"').strip("'").strip()
    return default


def _creds():
    ak = _get("BYTEPLUS_ACCESS_KEY", "BYTEPLUS_MODELARK_ACCESS_KEY", "BYTEPLUS_AK",
              "BYTEPLUS_ACCESS_KEY_ID", "ACCESS_KEY_ID", "ACCESSKEYID")
    sk = _get("BYTEPLUS_SECRET_KEY", "BYTEPLUS_MODELARK_SECRET_KEY", "BYTEPLUS_SK",
              "BYTEPLUS_SECRET_ACCESS_KEY", "SECRET_ACCESS_KEY", "SECRETACCESSKEY")
    token = _get("BYTEPLUS_SESSION_TOKEN", "BYTEPLUS_MODELARK_SESSION_TOKEN")
    return ak, sk, token


def is_configured() -> bool:
    ak, sk, _ = _creds()
    return bool(ak and sk)


def project_name() -> str:
    return _get("ASSET_PROJECT_NAME", default="default")


# ── BytePlus OpenAPI V4 signing ──────────────────────────────────────────────

def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _q(v: str) -> str:
    return quote(v, safe="-_.~")


def sign_request(*, ak, sk, token, method, host, query, payload, now,
                 region=REGION, service=SERVICE, content_type="application/json"):
    """Return the auth headers for one request (pure function — testable)."""
    request_date = now.strftime("%Y%m%dT%H%M%SZ")
    short_date = now.strftime("%Y%m%d")
    content_sha = _sha256_hex(payload)
    hv = {"host": host, "x-content-sha256": content_sha, "x-date": request_date}
    if method.upper() != "GET":
        hv["content-type"] = content_type
    if token:
        hv["x-security-token"] = token
    names = sorted(hv)
    canonical_headers = "".join(f"{n}:{hv[n].strip()}\n" for n in names)
    signed_headers = ";".join(names)
    canonical_query = "&".join(f"{_q(k)}={_q(v)}" for k, v in sorted(query.items()))
    canonical_request = "\n".join((method.upper(), "/", canonical_query,
                                   canonical_headers, signed_headers, content_sha))
    scope = f"{short_date}/{region}/{service}/request"
    string_to_sign = "\n".join(("HMAC-SHA256", request_date, scope,
                                _sha256_hex(canonical_request.encode("utf-8"))))
    key = sk.encode("utf-8")
    for part in (short_date, region, service, "request"):
        key = hmac.new(key, part.encode("utf-8"), hashlib.sha256).digest()
    signature = hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    headers = {
        "Host": host,
        "X-Date": request_date,
        "X-Content-Sha256": content_sha,
        "Authorization": (f"HMAC-SHA256 Credential={ak}/{scope}, "
                          f"SignedHeaders={signed_headers}, Signature={signature}"),
    }
    if "content-type" in hv:
        headers["Content-Type"] = content_type
    if token:
        headers["X-Security-Token"] = token
    return headers


class AssetLibraryError(RuntimeError):
    pass


def call(action: str, body: dict) -> dict:
    """POST one signed Action; return the unwrapped Result dict."""
    ak, sk, token = _creds()
    if not (ak and sk):
        raise AssetLibraryError("BYTEPLUS_ACCESS_KEY / BYTEPLUS_SECRET_KEY are not set in Secrets.")
    body = {k: v for k, v in body.items() if v is not None}
    payload = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    query = {"Action": action, "Version": VERSION}
    headers = sign_request(ak=ak, sk=sk, token=token, method="POST", host=HOST,
                           query=query, payload=payload, now=datetime.now(timezone.utc))
    headers["Accept"] = "application/json"
    r = requests.post(f"https://{HOST}/", params=query, data=payload,
                      headers=headers, timeout=60)
    try:
        data = r.json()
    except ValueError:
        data = None
    err = (data or {}).get("ResponseMetadata", {}).get("Error") if isinstance(data, dict) else None
    if r.status_code >= 400 or err:
        code = (err or {}).get("Code", "")
        msg = (err or {}).get("Message", "") or (r.text or "")[:300]
        hint = ""
        if "SignatureDoesNotMatch" in code or "InvalidAccessKey" in code or r.status_code == 401:
            hint = " — check BYTEPLUS_ACCESS_KEY / BYTEPLUS_SECRET_KEY in Secrets."
        elif "Forbidden" in code or "AccessDenied" in code or r.status_code == 403:
            hint = (" — the IAM user needs ArkFullAccess, and the account needs the free "
                    "'Advanced Creation Rights (Entry)' plan activated.")
        elif "Quota" in code or "Limit" in code:
            hint = f" — free plan allows {FREE_PLAN_LIMIT} assets; delete old characters to free space."
        raise AssetLibraryError(f"{action} failed [{r.status_code}] {code}: {msg}{hint}")
    result = (data or {}).get("Result")
    return result if isinstance(result, dict) else {}


# ── Groups ───────────────────────────────────────────────────────────────────

def list_groups(group_type="AIGC", name=None):
    items, token = [], None
    for _ in range(20):
        res = call("ListAssetGroups", {
            "Filter": {k: v for k, v in {"GroupType": group_type, "Name": name}.items() if v},
            "MaxResults": 100, "NextToken": token,
            "SortBy": "CreateTime", "SortOrder": "Desc",
            "ProjectName": project_name(),
        })
        items += [i for i in (res.get("Items") or []) if isinstance(i, dict)]
        token = res.get("NextToken")
        if not token:
            break
    return items


def create_group(name: str, description: str = "") -> str:
    res = call("CreateAssetGroup", {"Name": name[:64], "Description": description[:200] or None,
                                    "GroupType": "AIGC", "ProjectName": project_name()})
    gid = res.get("Id")
    if not gid:
        raise AssetLibraryError(f"CreateAssetGroup returned no Id: {res}")
    return gid


def ensure_group(name: str) -> str:
    """Reuse the AIGC group with exactly this name, or create it."""
    for g in list_groups("AIGC", name=name):
        if g.get("Name") == name:
            return g["Id"]
    return create_group(name)


def delete_group(group_id: str) -> None:
    call("DeleteAssetGroup", {"Id": group_id, "ProjectName": project_name()})


# ── Assets ───────────────────────────────────────────────────────────────────

_last_create = [0.0]


def create_asset(group_id: str, url: str, name: str = None, asset_type="Image") -> str:
    """CreateAsset (async). Spaced to the free plan's 3/min. Returns the asset Id."""
    wait = CREATE_ASSET_MIN_INTERVAL - (time.monotonic() - _last_create[0])
    if wait > 0:
        time.sleep(wait)
    _last_create[0] = time.monotonic()
    res = call("CreateAsset", {"GroupId": group_id, "URL": url, "AssetType": asset_type,
                               "Name": (name or None), "ProjectName": project_name()})
    aid = res.get("Id")
    if not aid:
        raise AssetLibraryError(f"CreateAsset returned no Id: {res}")
    return aid


def get_asset(asset_id: str) -> dict:
    return call("GetAsset", {"Id": asset_id, "ProjectName": project_name()})


def wait_active(asset_id: str, timeout=240, log=print) -> dict:
    """Poll until Active or Failed (or timeout). Returns the last GetAsset result."""
    start, last = time.time(), {}
    while time.time() - start < timeout:
        last = get_asset(asset_id)
        status = last.get("Status", "")
        if status in ("Active", "Failed"):
            return last
        log(f"    … {asset_id}: {status or 'Processing'}")
        time.sleep(5)
    return last


def list_assets(group_type="AIGC", group_ids=None, statuses=("Active",)):
    items, token = [], None
    for _ in range(20):
        res = call("ListAssets", {
            "Filter": {k: v for k, v in {"GroupType": group_type,
                                         "GroupIds": list(group_ids) if group_ids else None,
                                         "Statuses": list(statuses) if statuses else None}.items() if v},
            "MaxResults": 100, "NextToken": token,
            "SortBy": "CreateTime", "SortOrder": "Desc",
            "ProjectName": project_name(),
        })
        items += [i for i in (res.get("Items") or []) if isinstance(i, dict)]
        token = res.get("NextToken")
        if not token:
            break
    return items


def delete_asset(asset_id: str) -> None:
    call("DeleteAsset", {"Id": asset_id, "ProjectName": project_name()})


def usage_count() -> int:
    """Approximate number of assets counted against the plan (AIGC + Real-human)."""
    n = 0
    for gt in ("AIGC", "LivenessFace"):
        try:
            n += len(list_assets(gt, statuses=("Active", "Processing")))
        except AssetLibraryError:
            pass
    return n
