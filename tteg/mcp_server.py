from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .client import (
    TtegAPIError,
    TtegConnectionError,
    download_image,
    search_and_save_image as run_search_and_save_image,
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
    """Search Unsplash for real stock photos and return image URLs. Use this when a frontend task needs a hero image, team photo, or any real-world photo instead of placeholders."""
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
    """Download an image from a URL and save it to a local file path. Use after search_images to save a specific result into the project."""
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
    """Search for a stock photo and save it directly to a local file. Combines search + download in one step — ideal for adding a hero image or section photo to a project."""
    try:
        return run_search_and_save_image(
            query,
            output_path,
            index=index,
            orientation=orientation,
            width=width,
            height=height,
        )
    except (TtegConnectionError, TtegAPIError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool()
def batch_save_images(
    images: list[dict[str, Any]],
) -> dict[str, Any]:
    """Search and save multiple stock photos in one call. Pass an array of {query, output_path, orientation?} objects to fill an entire landing page with real photos at once."""
    try:
        saved: list[dict[str, Any]] = []
        for index, item in enumerate(images, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"item {index} must be an object")

            query = item.get("query")
            output_path = item.get("output_path")
            if not isinstance(query, str) or not query.strip():
                raise ValueError(f"item {index} is missing a valid query")
            if not isinstance(output_path, str) or not output_path.strip():
                raise ValueError(f"item {index} is missing a valid output_path")

            saved.append(
                run_search_and_save_image(
                    query.strip(),
                    output_path.strip(),
                    index=int(item.get("index", 1)),
                    orientation=item.get("orientation", "any"),
                    width=item.get("width"),
                    height=item.get("height"),
                )
            )

        return {"saved": saved}
    except (TtegConnectionError, TtegAPIError, ValueError, TypeError) as exc:
        raise RuntimeError(str(exc)) from exc


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
