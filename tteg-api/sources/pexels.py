from __future__ import annotations

from typing import Any

import requests

from models import ImageResult

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
DEFAULT_TIMEOUT_SECONDS = 15


def _build_image_url(src: dict[str, str], width: int | None, height: int | None) -> str:
    if width is not None or height is not None:
        base = src.get("original", "")
        if base:
            params: list[str] = []
            if width is not None:
                params.append(f"w={width}")
            if height is not None:
                params.append(f"h={height}")
            params.append("fit=crop")
            separator = "&" if "?" in base else "?"
            return f"{base}{separator}{'&'.join(params)}"
    return src.get("large2x") or src.get("large") or src.get("original") or ""


def _normalize_result(photo: dict[str, Any], width: int | None, height: int | None) -> ImageResult:
    src = photo.get("src") or {}
    return ImageResult(
        id=str(photo.get("id", "")),
        source="pexels",
        image_url=_build_image_url(src, width, height),
        thumb_url=src.get("medium") or src.get("small") or src.get("tiny") or "",
        photographer=photo.get("photographer"),
        width=photo.get("width"),
        height=photo.get("height"),
        title=photo.get("alt"),
        html_url=photo.get("url"),
        download_location=None,
    )


def search_pexels(
    *,
    api_key: str,
    query: str,
    count: int,
    orientation: str | None = None,
    width: int | None = None,
    height: int | None = None,
    session: requests.Session | None = None,
) -> list[ImageResult]:
    if not api_key:
        raise ValueError("Missing Pexels API key.")

    client = session or requests.Session()
    params: dict[str, Any] = {
        "query": query,
        "per_page": max(1, min(count, 30)),
    }
    if orientation and orientation not in ("any", "squarish"):
        params["orientation"] = orientation

    response = client.get(
        PEXELS_SEARCH_URL,
        params=params,
        headers={
            "Authorization": api_key,
            "User-Agent": "tteg-api/0.4.0",
        },
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    raw_photos = payload.get("photos") or []
    return [_normalize_result(photo, width, height) for photo in raw_photos if photo.get("src")]
