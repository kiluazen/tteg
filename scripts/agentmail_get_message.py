#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib import error, parse, request


DEFAULT_API_BASE = "https://api.agentmail.to/v0"
DEFAULT_INBOX_ID = "kushal@kushalsm.com"


def _candidate_env_paths() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    return [
        Path.cwd() / ".env",
        repo_root / ".env",
        repo_root.parent / ".env",
    ]


def _load_env_value(name: str) -> str | None:
    direct = os.environ.get(name)
    if direct:
        return direct

    for env_path in _candidate_env_paths():
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() != name:
                continue
            return value.strip().strip('"').strip("'")
    return None


def _get_json(url: str, api_key: str) -> dict:
    req = request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"AgentMail get failed with {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise SystemExit(f"AgentMail get failed: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch a full AgentMail message.")
    parser.add_argument("--message-id", required=True, help="Message id to fetch")
    parser.add_argument("--inbox-id", default=DEFAULT_INBOX_ID, help="AgentMail inbox id")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="AgentMail API base URL")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Fetch raw metadata instead of parsed message content",
    )
    args = parser.parse_args()

    api_key = _load_env_value("KUSHALSM_AGENTMAIL")
    if not api_key:
        raise SystemExit("Missing KUSHALSM_AGENTMAIL in env or nearby .env files.")

    encoded_inbox = parse.quote(args.inbox_id, safe="")
    encoded_message = parse.quote(args.message_id, safe="")
    suffix = "/raw" if args.raw else ""
    url = f"{args.api_base.rstrip('/')}/inboxes/{encoded_inbox}/messages/{encoded_message}{suffix}"
    payload = _get_json(url, api_key)
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
