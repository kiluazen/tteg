from __future__ import annotations

from typing import Any

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

    try:
        response = requests.get(
            f"{base_url}/search",
            params=params,
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
