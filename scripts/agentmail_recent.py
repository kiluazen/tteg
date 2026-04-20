#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
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


def _get_messages(api_key: str, inbox_id: str, limit: int, api_base: str) -> dict[str, Any]:
    qs = parse.urlencode({"limit": limit})
    url = f"{api_base.rstrip('/')}/inboxes/{parse.quote(inbox_id, safe='')}/messages?{qs}"
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
        raise SystemExit(f"AgentMail list failed with {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise SystemExit(f"AgentMail list failed: {exc}") from exc


def _print_message(message: dict[str, Any]) -> None:
    labels = ",".join(message.get("labels", []))
    subject = message.get("subject", "").replace("\n", " ").strip()
    print(
        "\t".join(
            [
                str(message.get("timestamp", "")),
                str(message.get("from", "")),
                subject,
                labels,
                str(message.get("message_id", "")),
            ]
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="List recent AgentMail messages.")
    parser.add_argument("--limit", type=int, default=20, help="Number of messages to fetch")
    parser.add_argument("--inbox-id", default=DEFAULT_INBOX_ID, help="AgentMail inbox id")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="AgentMail API base URL")
    parser.add_argument(
        "--external-only",
        action="store_true",
        help="Only show messages not sent from the inbox itself",
    )
    args = parser.parse_args()

    api_key = _load_env_value("KUSHALSM_AGENTMAIL")
    if not api_key:
        raise SystemExit("Missing KUSHALSM_AGENTMAIL in env or nearby .env files.")

    payload = _get_messages(
        api_key=api_key,
        inbox_id=args.inbox_id,
        limit=args.limit,
        api_base=args.api_base,
    )
    print("timestamp\tfrom\tsubject\tlabels\tmessage_id")
    for message in payload.get("messages", []):
        if args.external_only and args.inbox_id in str(message.get("from", "")):
            continue
        _print_message(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
