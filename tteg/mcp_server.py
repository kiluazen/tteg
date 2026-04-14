from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .client import (
    TtegAPIError,
    TtegConnectionError,
    download_image,
    search_images as run_search_images,
)

mcp = FastMCP("tteg", json_response=True)


@mcp.tool()
def search_images(
    query: str,
    count: int = 5,
    orientation: Literal["any", "landscape", "portrait", "square"] = "any",
    width: int | None = None,
    height: int | None = None,
) -> dict[str, Any]:
    """Return real stock photo URLs from tteg."""
    try:
        return run_search_images(
            query,
            count=count,
            orientation=orientation,
            width=width,
            height=height,
        )
    except (TtegConnectionError, TtegAPIError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool()
def save_image(
    url: str,
    output_path: str,
) -> dict[str, Any]:
    """Download an image URL to a local path."""
    try:
        return download_image(url, output_path)
    except (TtegConnectionError, TtegAPIError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool()
def search_and_save_image(
    query: str,
    output_path: str,
    index: int = 1,
    orientation: Literal["any", "landscape", "portrait", "square"] = "any",
    width: int | None = None,
    height: int | None = None,
) -> dict[str, Any]:
    """Search tteg and save one result locally."""
    try:
        payload = run_search_images(
            query,
            count=index,
            orientation=orientation,
            width=width,
            height=height,
        )
        results = payload.get("results")
        if not isinstance(results, list) or len(results) < index:
            raise ValueError(f"expected at least {index} results for query '{query}'")

        selected = results[index - 1]
        if not isinstance(selected, dict):
            raise ValueError("server returned an invalid result shape")

        image_url = selected.get("image_url")
        if not isinstance(image_url, str) or not image_url.strip():
            raise ValueError("selected result did not include an image_url")

        saved = download_image(image_url, output_path)
        return {
            "query": query,
            "saved_to": saved["output_path"],
            "content_type": saved["content_type"],
            "size_bytes": saved["size_bytes"],
            "result": selected,
        }
    except (TtegConnectionError, TtegAPIError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
