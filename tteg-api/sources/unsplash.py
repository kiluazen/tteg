from __future__ import annotations

from typing import Any

import requests

from models import ImageResult

UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"
DEFAULT_TIMEOUT_SECONDS = 15


def _build_image_url(raw_url: str | None, fallback_url: str | None, width: int | None, height: int | None) -> str:
    if width is None and height is None:
        return fallback_url or raw_url or ""

    if not raw_url:
        return fallback_url or ""

    params: list[str] = []
    if width is not None:
        params.append(f"w={width}")
    if height is not None:
        params.append(f"h={height}")
    if width is not None and height is not None:
        params.append("fit=crop")
    else:
        params.append("fit=max")
    params.append("q=80")
    separator = "&" if "?" in raw_url else "?"
    return f"{raw_url}{separator}{'&'.join(params)}"


def _normalize_result(photo: dict[str, Any], width: int | None, height: int | None) -> ImageResult:
    urls = photo.get("urls") or {}
    links = photo.get("links") or {}
    user = photo.get("user") or {}
    title = photo.get("description") or photo.get("alt_description")

    return ImageResult(
        id=str(photo.get("id", "")),
        source="unsplash",
        image_url=_build_image_url(urls.get("raw"), urls.get("regular"), width, height),
        thumb_url=urls.get("thumb") or urls.get("small") or urls.get("regular") or "",
        photographer=user.get("name"),
        width=photo.get("width"),
        height=photo.get("height"),
        title=title,
        html_url=links.get("html"),
        download_location=links.get("download_location"),
    )


def search_unsplash(
    *,
    access_key: str,
    query: str,
    count: int,
    orientation: str | None = None,
    width: int | None = None,
    height: int | None = None,
    session: requests.Session | None = None,
) -> list[ImageResult]:
    if not access_key:
        raise ValueError("Missing Unsplash access key.")

    client = session or requests.Session()
    params: dict[str, Any] = {
        "query": query,
        "per_page": max(1, min(count, 30)),
    }
    if orientation and orientation != "any":
        params["orientation"] = "squarish" if orientation == "square" else orientation

    response = client.get(
        UNSPLASH_SEARCH_URL,
        params=params,
        headers={
            "Authorization": f"Client-ID {access_key}",
            "Accept-Version": "v1",
            "User-Agent": "tteg-api/0.2.0",
        },
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    raw_results = payload.get("results") or []
    return [_normalize_result(item, width, height) for item in raw_results if item.get("urls")]
