# tteg

[![PyPI version](https://img.shields.io/pypi/v/tteg)](https://pypi.org/project/tteg/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/tteg)](https://pypi.org/project/tteg/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/kiluazen/tteg/blob/main/LICENSE)
[![CI](https://github.com/kiluazen/tteg/actions/workflows/ci.yml/badge.svg)](https://github.com/kiluazen/tteg/actions/workflows/ci.yml)

Unsplash stock photos without registration or API keys.

```bash
uv tool install tteg
tteg save "startup office" ./public/hero --orientation landscape
# → saves a real photo to ./public/hero.jpg
```

No Unsplash app. No API key. No `.env` files. Just photos.

## Why this exists

Unsplash has 4M+ free photos. To use them programmatically you need to register a developer account, create an application, and manage API keys. Their official JavaScript library was [archived in 2024](https://github.com/unsplash/unsplash-js).

Meanwhile `source.unsplash.com/random` — the zero-setup alternative everyone used — was deprecated in mid-2024 and now 503s. An authenticated GitHub code-search returns ~16,500 live file hits across ~885 unique repositories still referencing it; see [RESEARCH.md](RESEARCH.md) for the full list, including several 1k+ star projects currently shipping broken `<img>` tags.

tteg handles all of that server-side. You get a CLI, an HTTP API, an MCP server, and an embeddable widget — all with zero setup.

## Install

```bash
uv tool install tteg
# or: pip install tteg
```

## Use

**Search** — get image URLs:
```bash
tteg "coffee shop" -n 3 --orientation landscape
```

**Save** — download one photo into your project:
```bash
tteg save "modern office" ./public/hero --orientation landscape
```

**Batch** — fill an entire landing page from a JSON manifest:
```bash
tteg batch landing-page-images.json
```

```json
[
  {"query": "startup office", "output": "./public/hero", "orientation": "landscape"},
  {"query": "developer portrait", "output": "./public/founder"},
  {"query": "team meeting", "output": "./public/team", "orientation": "landscape"}
]
```

## HTTP API (no install needed)

```bash
curl "https://tteg-api-53227342417.asia-south1.run.app/search?q=coffee+shop&n=3"
```

No headers. No auth. CORS enabled. [Try it live →](https://tteg.kushalsm.com/try)

**Parameters:** `q` (query), `n` (count, 1-10), `orientation` (landscape/portrait/square/any), `width`, `height`

## MCP server

For Claude Code, Cursor, or any MCP host:

```json
{
  "mcpServers": {
    "tteg": {
      "command": "uvx",
      "args": ["tteg-mcp"]
    }
  }
}
```

Tools: `search_images`, `save_image`, `search_and_save_image`, `batch_save_images`

## Embed widget

Drop into any HTML page:

```html
<div data-tteg="coffee shop" data-count="3"></div>
<script src="https://tteg.kushalsm.com/embed.js"></script>
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-n`, `--count` | 5 | Number of results (1–10) |
| `--orientation` | any | `landscape`, `portrait`, `square`, or `any` |
| `--width` | — | Max width in pixels |
| `--height` | — | Max height in pixels |

## Starter kit

Copy-paste blocks for CLAUDE.md and AGENTS.md: [STARTER_KIT.md](STARTER_KIT.md)

## Links

- [tteg.kushalsm.com](https://tteg.kushalsm.com) — landing page
- [Try it live](https://tteg.kushalsm.com/try) — search from your browser
- [PyPI](https://pypi.org/project/tteg/) — `pip install tteg`
- Free tier: 50 queries/day per IP
