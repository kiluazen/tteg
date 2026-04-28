from __future__ import annotations

import os
import random
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import requests

from models import ImageResult
from sources.unsplash import search_unsplash
import db

app = FastAPI(title="tteg-api", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

LANDING_URL = "https://tteg.kushalsm.com"


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _resolve_access_keys() -> list[str]:
    """Return all configured Unsplash access keys.

    Reads from (in order):
      UNSPLASH_ACCESS_KEYS — comma-separated list of keys
      UNSPLASH_ACCESS_KEY  — primary key (backward compat)
      UNSPLASH_ACCESS_KEY_2, _3, ... — additional numbered keys
      ACCESS_KEY           — legacy fallback
    """
    keys: list[str] = []

    pool = os.environ.get("UNSPLASH_ACCESS_KEYS", "")
    if pool:
        keys.extend(k.strip() for k in pool.split(",") if k.strip())

    for name in ("UNSPLASH_ACCESS_KEY", "ACCESS_KEY"):
        k = os.environ.get(name, "").strip()
        if k and k not in keys:
            keys.append(k)

    i = 2
    while True:
        k = os.environ.get(f"UNSPLASH_ACCESS_KEY_{i}", "").strip()
        if not k:
            break
        if k not in keys:
            keys.append(k)
        i += 1

    return keys


def _pick_access_key(keys: list[str]) -> str:
    """Pick a random key from the pool for even distribution across Cloud Run instances."""
    if not keys:
        return ""
    return random.choice(keys)


def _serialize_result(result: ImageResult, index: int) -> dict[str, object]:
    return {
        "id": index,
        "title": result.title,
        "image_url": result.image_url,
        "thumb_url": result.thumb_url,
    }


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.on_event("startup")
def startup() -> None:
    _load_local_env()


# ── health / auth config ────────────────────────────────────────────────────


@app.get("/")
def root() -> dict[str, object]:
    return {
        "name": "tteg-api",
        "version": "0.4.0",
        "description": "Unsplash stock photos — signup and use, no API keys",
        "try_it": "GET /search?q=coffee+shop&n=3",
        "parameters": {
            "q": "search query (required)",
            "n": "number of results, 1-10 (default: 5)",
            "orientation": "landscape | portrait | square | any (default: any)",
            "width": "max width in pixels",
            "height": "max height in pixels",
        },
        "auth": "Bearer token from tteg auth login (or free tier: 50 queries/day per IP)",
        "website": LANDING_URL,
        "demo": f"{LANDING_URL}/try",
        "source": "https://github.com/kiluazen/tteg",
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/config")
def auth_config() -> dict[str, object]:
    supabase_url = os.environ.get("SUPABASE_URL", "")
    publishable_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    auth_enabled = bool(supabase_url and publishable_key)
    return {
        "auth_enabled": auth_enabled,
        "supabase_url": supabase_url,
        "supabase_publishable_key": publishable_key,
    }


# ── search ───────────────────────────────────────────────────────────────────


@app.get("/search")
def search(
    request: Request,
    q: str,
    n: int = Query(default=5, ge=1, le=10),
    orientation: str = Query(default="any", pattern="^(any|landscape|portrait|square)$"),
    width: int | None = Query(default=None, ge=1, le=10000),
    height: int | None = Query(default=None, ge=1, le=10000),
) -> dict[str, object]:
    # ── resolve user from auth header ───────────────────────────────────────
    bearer = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    user = None

    if bearer:
        user = db.verify_supabase_token(bearer)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token. Run: tteg auth login")

    if user:
        # Authenticated user — track by user ID, no rate limit for now
        db.track_user_request(user["id"], q)
    else:
        # Anonymous / free tier — enforce daily query limit per IP
        client_ip = _get_client_ip(request)
        allowed, _count = db.check_and_increment_usage(client_ip)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Free tier limit ({db.FREE_DAILY_LIMIT} queries/day) reached. "
                    f"Sign up for unlimited access: tteg auth login"
                ),
            )

    # ── Unsplash search ─────────────────────────────────────────────────────
    access_key = _pick_access_key(_resolve_access_keys())
    if not access_key:
        raise HTTPException(status_code=500, detail="UNSPLASH_ACCESS_KEY is not configured")

    try:
        results = search_unsplash(
            access_key=access_key,
            query=q,
            count=n,
            orientation=orientation,
            width=width,
            height=height,
        )
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        detail = exc.response.text if exc.response is not None and exc.response.text else str(exc)
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload: dict[str, object] = {
        "query": q,
        "results": [_serialize_result(result, index) for index, result in enumerate(results, start=1)],
    }
    if not user:
        payload["_tier"] = "free"
        payload["_signup"] = "Run 'tteg auth login' for unlimited access"

    _track_downloads(results, access_key)
    return payload


def _track_downloads(results: list[ImageResult], access_key: str) -> None:
    for result in results:
        if not result.download_location:
            continue
        try:
            requests.get(
                result.download_location,
                headers={"Authorization": f"Client-ID {access_key}"},
                timeout=5,
            )
        except Exception:
            pass
