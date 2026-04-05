from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
import requests

from models import ImageResult
from sources.unsplash import search_unsplash

app = FastAPI(title="tteg-api", version="0.2.0")


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


def _resolve_access_key() -> str:
    return os.environ.get("UNSPLASH_ACCESS_KEY") or os.environ.get("ACCESS_KEY") or ""


def _serialize_result(result: ImageResult, index: int) -> dict[str, object]:
    return {
        "id": index,
        "title": result.title,
        "image_url": result.image_url,
        "thumb_url": result.thumb_url,
    }


@app.on_event("startup")
def startup() -> None:
    _load_local_env()


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


@app.get("/search")
def search(
    q: str,
    n: int = Query(default=5, ge=1, le=10),
    orientation: str = Query(default="any", pattern="^(any|landscape|portrait|square)$"),
    width: int | None = Query(default=None, ge=1, le=10000),
    height: int | None = Query(default=None, ge=1, le=10000),
) -> dict[str, object]:
    access_key = _resolve_access_key()
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

    # Unsplash API guidelines: trigger download tracking for returned results
    _track_downloads(results, access_key)

    return payload


def _track_downloads(results: list[ImageResult], access_key: str) -> None:
    """Ping Unsplash download_location URLs in the background for API compliance."""
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
            pass  # best-effort, don't fail the request
