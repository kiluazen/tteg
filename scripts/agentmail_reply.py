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


def _read_text_arg(text: str | None, text_file: str | None) -> str:
    if bool(text) == bool(text_file):
        raise SystemExit("Provide exactly one of --text or --text-file.")
    if text is not None:
        return text
    return Path(text_file).read_text(encoding="utf-8")


def _post_reply(
    api_key: str,
    inbox_id: str,
    message_id: str,
    text: str,
    api_base: str,
    reply_all: bool,
) -> dict[str, Any]:
    encoded_inbox = parse.quote(inbox_id, safe="")
    encoded_message = parse.quote(message_id, safe="")
    action = "reply-all" if reply_all else "reply"
    url = f"{api_base.rstrip('/')}/inboxes/{encoded_inbox}/messages/{encoded_message}/{action}"
    body = json.dumps({"text": text}).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"AgentMail reply failed with {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise SystemExit(f"AgentMail reply failed: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Reply to an AgentMail message.")
    parser.add_argument("--message-id", required=True, help="Inbound message id to reply to")
    parser.add_argument("--text", help="Plain-text body")
    parser.add_argument("--text-file", help="Path to a file containing the plain-text body")
    parser.add_argument(
        "--reply-all",
        action="store_true",
        help="Reply to all recipients instead of only the sender",
    )
    parser.add_argument("--inbox-id", default=DEFAULT_INBOX_ID, help="AgentMail inbox id")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="AgentMail API base URL")
    args = parser.parse_args()

    api_key = _load_env_value("KUSHALSM_AGENTMAIL")
    if not api_key:
        raise SystemExit("Missing KUSHALSM_AGENTMAIL in env or nearby .env files.")

    text = _read_text_arg(args.text, args.text_file)
    response = _post_reply(
        api_key=api_key,
        inbox_id=args.inbox_id,
        message_id=args.message_id,
        text=text,
        api_base=args.api_base,
        reply_all=args.reply_all,
    )
    json.dump(response, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
