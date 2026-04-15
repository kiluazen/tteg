from __future__ import annotations

import json
import os
import re
import stat
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, parse, request

import click

from ._version import __version__
from .client import (
    DEFAULT_API_URL,
    TtegAPIError,
    TtegConnectionError,
    resolve_api_url,
    search_and_save_image,
    search_images,
)
CONFIG_DIR = Path.home() / ".config" / "tteg"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"


def _resolve_api_url() -> str:
    return resolve_api_url()


# ------------------------------------------------------------------ CLI group


class _DefaultGroup(click.Group):
    """A click.Group that routes unknown first args to the 'search' subcommand."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if args and args[0] not in self.commands and not args[0].startswith("-"):
            args = ["search"] + args
        return super().parse_args(ctx, args)


@click.group(
    cls=_DefaultGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=__version__, prog_name="tteg")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Free stock image search CLI for agents."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ------------------------------------------------------------------- search


@main.command()
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
def search(
    query: str,
    count: int,
    orientation: str,
    width: int | None,
    height: int | None,
) -> None:
    """Send a search request to the tteg API and print the JSON response."""
    try:
        payload = search_images(
            query,
            count=count,
            orientation=orientation,
            width=width,
            height=height,
        )
    except TtegConnectionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    except TtegAPIError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(json.dumps(payload, indent=2))
    return


@main.command()
@click.argument("query")
@click.argument("output", type=click.Path(path_type=Path))
@click.option("--index", default=1, show_default=True, type=click.IntRange(1, 10))
@click.option(
    "--orientation",
    type=click.Choice(["any", "landscape", "portrait", "square"], case_sensitive=False),
    default="any",
    show_default=True,
)
@click.option("--width", type=click.IntRange(1, 10000), default=None)
@click.option("--height", type=click.IntRange(1, 10000), default=None)
def save(
    query: str,
    output: Path,
    index: int,
    orientation: str,
    width: int | None,
    height: int | None,
) -> None:
    """Search and save one image locally."""
    try:
        payload = search_and_save_image(query, output, index=index, orientation=orientation, width=width, height=height)
    except click.ClickException as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc
    except TtegConnectionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc
    except TtegAPIError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc

    click.echo(json.dumps(payload, indent=2))
    click.echo("\n  saved via tteg — github.com/kiluazen/tteg", err=True)


@main.command()
@click.argument("manifest", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def batch(manifest: Path) -> None:
    """Save many images from a JSON manifest."""
    try:
        items = _load_batch_manifest(manifest)
        saved: list[dict[str, Any]] = []
        for item in items:
            saved.append(
                search_and_save_image(
                    item["query"],
                    item["output"],
                    index=item["index"],
                    orientation=item["orientation"],
                    width=item["width"],
                    height=item["height"],
                )
            )
    except click.ClickException as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc
    except TtegConnectionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc
    except TtegAPIError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc

    click.echo(
        json.dumps(
            {
                "manifest": str(manifest),
                "saved": saved,
            },
            indent=2,
        )
    )
    click.echo(f"\n  {len(saved)} images saved via tteg — github.com/kiluazen/tteg", err=True)


@main.command("mcp")
def run_mcp() -> None:
    """Run the stdio MCP server."""
    from .mcp_server import main as run_server

    run_server()


# --------------------------------------------------------------------- auth


@main.group()
def auth() -> None:
    """Manage authentication."""


@auth.command()
@click.argument("email")
@click.option("--code", default=None, help="6-digit code from email (skip interactive prompt)")
@click.option("--base-url", default=None, help="tteg API base URL")
def login(email: str, code: str | None, base_url: str | None) -> None:
    """Sign in with email. Sends a 6-digit code to your inbox."""
    api_url = base_url or _resolve_api_url()

    auth_config = _fetch_auth_config(api_url)
    if not auth_config.get("auth_enabled"):
        click.echo("Error: auth is not enabled on this tteg server.", err=True)
        raise SystemExit(1)

    supabase_url = auth_config.get("supabase_url")
    publishable_key = auth_config.get("supabase_publishable_key")
    if not supabase_url or not publishable_key:
        click.echo("Error: server did not return valid auth configuration.", err=True)
        raise SystemExit(1)

    if code is None:
        # Step 1: send OTP to email
        _http_json(
            "POST",
            f"{supabase_url.rstrip('/')}/auth/v1/otp",
            body={"email": email},
            extra_headers={"apikey": publishable_key},
        )
        click.echo(f"Sent a 6-digit code to {email}")
        code = click.prompt("Enter code")

    # Step 2: verify OTP and get session
    token_response = _http_json(
        "POST",
        f"{supabase_url.rstrip('/')}/auth/v1/verify",
        body={"email": email, "token": code, "type": "email"},
        extra_headers={"apikey": publishable_key},
    )

    access_token = token_response.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        click.echo("Error: invalid code or verification failed.", err=True)
        raise SystemExit(1)

    expires_at = token_response.get("expires_at")
    if expires_at is None:
        expires_in = token_response.get("expires_in")
        if isinstance(expires_in, (int, float)):
            expires_at = int(time.time() + float(expires_in))

    user_info = token_response.get("user") or {}
    user_email = user_info.get("email", email)

    _save_credentials(
        {
            "base_url": api_url,
            "access_token": access_token.strip(),
            "refresh_token": token_response.get("refresh_token"),
            "expires_at": expires_at,
            "supabase_url": supabase_url,
            "supabase_publishable_key": publishable_key,
        }
    )

    click.echo(f"Logged in as {user_email}")


@auth.command()
def status() -> None:
    """Check current auth status."""
    creds = _load_credentials()
    if creds is None:
        click.echo(json.dumps({"logged_in": False}, indent=2))
        return

    token = _cred_str(creds, "access_token")
    if not token:
        click.echo(json.dumps({"logged_in": False}, indent=2))
        return

    expires_at = _cred_number(creds, "expires_at")
    expired = expires_at is not None and time.time() >= expires_at

    click.echo(
        json.dumps(
            {
                "logged_in": True,
                "base_url": _cred_str(creds, "base_url"),
                "token_expired": expired,
            },
            indent=2,
        )
    )


@auth.command()
def logout() -> None:
    """Sign out and remove credentials."""
    if CREDENTIALS_PATH.exists():
        CREDENTIALS_PATH.unlink()
    click.echo(json.dumps({"logged_out": True}, indent=2))


# -------------------------------------------------------------- HTTP helpers


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    if query:
        clean = {k: v for k, v in query.items() if v is not None}
        if clean:
            url = f"{url}?{parse.urlencode(clean)}"

    headers: dict[str, str] = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    if extra_headers:
        headers.update(extra_headers)

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = request.Request(url, data=data, headers=headers, method=method)

    try:
        with request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        click.echo(f"Error: HTTP {exc.code}: {details}", err=True)
        raise SystemExit(1) from exc
    except error.URLError as exc:
        click.echo(f"Error: failed to reach server: {exc.reason}", err=True)
        raise SystemExit(1) from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        click.echo(f"Error: server returned invalid JSON: {raw[:200]}", err=True)
        raise SystemExit(1) from exc


def _fetch_auth_config(api_url: str) -> dict[str, Any]:
    return _http_json("GET", f"{api_url.rstrip('/')}/auth/config")


# ---------------------------------------------------------- credential store


def _load_credentials() -> dict[str, Any] | None:
    if not CREDENTIALS_PATH.exists():
        return None
    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, dict) else None


def _save_credentials(payload: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.chmod(CREDENTIALS_PATH, stat.S_IRUSR | stat.S_IWUSR)


def _cred_str(creds: dict[str, Any] | None, key: str) -> str | None:
    if creds is None:
        return None
    val = creds.get(key)
    return val.strip() if isinstance(val, str) and val.strip() else None


def _cred_number(creds: dict[str, Any] | None, key: str) -> float | None:
    if creds is None:
        return None
    val = creds.get(key)
    return float(val) if isinstance(val, (int, float)) else None


# ----------------------------------------------------------- misc helpers


def _load_batch_manifest(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise click.ClickException(f"failed to read manifest: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"manifest is not valid JSON: {exc}") from exc

    if isinstance(payload, dict):
        payload = payload.get("images")

    if not isinstance(payload, list) or not payload:
        raise click.ClickException("manifest must be a non-empty JSON array or an object with an images array")

    items: list[dict[str, Any]] = []
    for index, raw_item in enumerate(payload, start=1):
        if not isinstance(raw_item, dict):
            raise click.ClickException(f"manifest item {index} must be an object")

        query = raw_item.get("query")
        output = raw_item.get("output")
        if not isinstance(query, str) or not query.strip():
            raise click.ClickException(f"manifest item {index} is missing a valid query")
        if not isinstance(output, str) or not output.strip():
            raise click.ClickException(f"manifest item {index} is missing a valid output path")

        item_index = raw_item.get("index", 1)
        if not isinstance(item_index, int) or not 1 <= item_index <= 10:
            raise click.ClickException(f"manifest item {index} index must be an integer between 1 and 10")

        orientation = raw_item.get("orientation", "any")
        if orientation not in {"any", "landscape", "portrait", "square"}:
            raise click.ClickException(
                f"manifest item {index} orientation must be one of: any, landscape, portrait, square"
            )

        width = raw_item.get("width")
        height = raw_item.get("height")
        for label, value in [("width", width), ("height", height)]:
            if value is not None and (not isinstance(value, int) or value < 1):
                raise click.ClickException(f"manifest item {index} {label} must be a positive integer")

        items.append(
            {
                "query": query.strip(),
                "output": Path(output),
                "index": item_index,
                "orientation": orientation,
                "width": width,
                "height": height,
            }
        )

    return items


if __name__ == "__main__":
    main()
