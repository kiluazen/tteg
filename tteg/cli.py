from __future__ import annotations

import json
import os

import click
import requests

from ._version import __version__

DEFAULT_API_URL = "https://tteg-api-53227342417.asia-south1.run.app"


def _resolve_api_url() -> str:
    return os.environ.get("TTEG_API_URL", DEFAULT_API_URL).rstrip("/")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="tteg")
@click.argument("query")
@click.option("-n", "--count", default=5, show_default=True, type=click.IntRange(1, 10))
@click.option(
    "--orientation",
    type=click.Choice(["any", "landscape", "portrait", "square"], case_sensitive=False),
    default="any",
    show_default=True,
)
@click.option("--width", type=click.IntRange(1, 10000), default=None)
@click.option("--height", type=click.IntRange(1, 10000), default=None)
def main(
    query: str,
    count: int,
    orientation: str,
    width: int | None,
    height: int | None,
) -> None:
    """Send a search request to the tteg API and print the JSON response."""
    api_url = _resolve_api_url()
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
            f"{api_url}/search",
            params=params,
            timeout=30,
        )
    except requests.RequestException as exc:
        click.echo(f"Error: failed to reach tteg API at {api_url}: {exc}", err=True)
        raise SystemExit(1)

    if response.ok:
        click.echo(json.dumps(response.json(), indent=2))
        return

    try:
        error_payload = response.json()
    except ValueError:
        error_payload = {"detail": response.text.strip() or "unknown error"}

    detail = error_payload.get("detail", error_payload)
    click.echo(f"Error: tteg API returned {response.status_code}: {detail}", err=True)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
