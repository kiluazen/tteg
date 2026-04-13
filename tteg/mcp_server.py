from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .client import TtegAPIError, TtegConnectionError, search_images as run_search_images

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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
