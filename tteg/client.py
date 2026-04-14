from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

DEFAULT_API_URL = "https://tteg-api-53227342417.asia-south1.run.app"
VALID_ORIENTATIONS = {"any", "landscape", "portrait", "square"}


class TtegError(RuntimeError):
    """Base error for tteg client failures."""


class TtegConnectionError(TtegError):
    """Raised when the API cannot be reached."""


class TtegAPIError(TtegError):
    """Raised when the API returns an error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"tteg API returned {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


def resolve_api_url() -> str:
    import os

    return os.environ.get("TTEG_API_URL", DEFAULT_API_URL).rstrip("/")


def _load_auth_token() -> str | None:
    """Read the saved access token from ~/.config/tteg/credentials.json."""
    import json

    creds_path = Path.home() / ".config" / "tteg" / "credentials.json"
    if not creds_path.exists():
        return None
    try:
        data = json.loads(creds_path.read_text(encoding="utf-8"))
        return data.get("access_token")
    except Exception:
        return None


def search_images(
    query: str,
    *,
    count: int = 5,
    orientation: str = "any",
    width: int | None = None,
    height: int | None = None,
    api_url: str | None = None,
    timeout: float = 30,
) -> dict[str, Any]:
    if not 1 <= count <= 10:
        raise ValueError("count must be between 1 and 10")
    if orientation not in VALID_ORIENTATIONS:
        raise ValueError(f"orientation must be one of: {', '.join(sorted(VALID_ORIENTATIONS))}")

    base_url = (api_url or resolve_api_url()).rstrip("/")
    params: dict[str, object] = {
        "q": query,
        "n": count,
        "orientation": orientation,
    }
    if width is not None:
        params["width"] = width
    if height is not None:
        params["height"] = height

    headers: dict[str, str] = {}
    token = _load_auth_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(
            f"{base_url}/search",
            params=params,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise TtegConnectionError(f"failed to reach tteg API at {base_url}: {exc}") from exc

    if response.ok:
        try:
            payload = response.json()
        except ValueError as exc:
            raise TtegAPIError(response.status_code, "server returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise TtegAPIError(response.status_code, "server returned unexpected response shape")
        return payload

    try:
        error_payload = response.json()
    except ValueError:
        detail = response.text.strip() or "unknown error"
    else:
        detail = error_payload.get("detail", error_payload) if isinstance(error_payload, dict) else error_payload

    raise TtegAPIError(response.status_code, str(detail))


def download_image(
    url: str,
    output_path: str | Path,
    *,
    timeout: float = 30,
) -> dict[str, Any]:
    destination = Path(output_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        raise TtegConnectionError(f"failed to download image from {url}: {exc}") from exc

    if not response.ok:
        detail = response.text.strip() or "download failed"
        raise TtegAPIError(response.status_code, detail)

    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    final_path = _finalize_output_path(destination, url, content_type)
    final_path.write_bytes(response.content)

    return {
        "output_path": str(final_path),
        "content_type": content_type or None,
        "size_bytes": len(response.content),
    }


def search_and_save_image(
    query: str,
    output_path: str | Path,
    *,
    index: int = 1,
    orientation: str = "any",
    width: int | None = None,
    height: int | None = None,
    timeout: float = 30,
) -> dict[str, Any]:
    payload = search_images(
        query,
        count=index,
        orientation=orientation,
        width=width,
        height=height,
        timeout=timeout,
    )
    selected = select_search_result(payload, index)

    image_url = selected.get("image_url")
    if not isinstance(image_url, str) or not image_url.strip():
        raise ValueError("selected result did not include an image_url")

    target = _resolve_output_path(Path(output_path), selected, index)
    saved = download_image(image_url, target, timeout=timeout)
    return {
        "query": query,
        "saved_to": saved["output_path"],
        "content_type": saved["content_type"],
        "size_bytes": saved["size_bytes"],
        "result": selected,
    }


def select_search_result(payload: dict[str, Any], index: int) -> dict[str, Any]:
    results = payload.get("results")
    if not isinstance(results, list) or len(results) < index:
        raise ValueError(f"expected at least {index} results for query '{payload.get('query', '')}'")

    selected = results[index - 1]
    if not isinstance(selected, dict):
        raise ValueError("server returned an invalid result shape")

    return selected


def _resolve_output_path(output: Path, selected: dict[str, Any], index: int) -> Path:
    if output.exists() and output.is_dir():
        return output / _default_filename(selected, index)
    return output


def _default_filename(selected: dict[str, Any], index: int) -> str:
    title = selected.get("title")
    if isinstance(title, str) and title.strip():
        stem = _slugify(title)
    else:
        stem = f"tteg-image-{index}"
    return stem or f"tteg-image-{index}"


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned[:80] or "tteg-image"


def _finalize_output_path(path: Path, url: str, content_type: str) -> Path:
    if path.suffix:
        return path

    inferred = _infer_extension(url, content_type)
    if inferred:
        return path.with_suffix(inferred)
    return path


def _infer_extension(url: str, content_type: str) -> str:
    if content_type:
        guessed = mimetypes.guess_extension(content_type)
        if guessed == ".jpe":
            return ".jpg"
        if guessed:
            return guessed

    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix:
        return ".jpg" if suffix == ".jpeg" else suffix

    return ""
