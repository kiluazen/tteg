# tteg

Free stock image search CLI and MCP server for AI coding agents. No API keys, no setup.

```bash
uv tool install tteg && tteg "mountain sunset"
```

Returns image URLs from Unsplash — ready to drop into any LLM workflow.

## Install

```bash
uv tool install tteg
# or: pip install tteg
```

## Usage

```bash
tteg "mountain sunset"
tteg "hero banner" -n 8 --orientation landscape
tteg "office workspace" --width 1920 --height 1080
tteg save "saas team working" ./public/hero
```

## Output

```json
{
  "query": "mountain sunset",
  "results": [
    {
      "id": 1,
      "title": "A colorful sunrise over Jamnik village",
      "image_url": "https://images.unsplash.com/photo-...",
      "thumb_url": "https://images.unsplash.com/photo-...&w=200"
    },
    {
      "id": 2,
      "title": "Brown mountains under orange sky",
      "image_url": "https://images.unsplash.com/photo-...",
      "thumb_url": "https://images.unsplash.com/photo-...&w=200"
    }
  ]
}
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-n`, `--count` | 5 | Number of results (1–10) |
| `--orientation` | any | `landscape`, `portrait`, `square`, or `any` |
| `--width` | — | Target width in pixels |
| `--height` | — | Target height in pixels |

## Save Locally

```bash
tteg save "saas team working" ./public/hero
tteg save "workspace desk" ./public/images/hero.jpg --orientation landscape
```

`tteg save` searches, picks one result, downloads it locally, and prints JSON with the saved path.

## Why

Agents frequently need real images — hero banners, product shots, blog headers. The normal path (register for Unsplash, get an API key, handle rate limits) is too much friction for a mid-task agent call.

`tteg` abstracts all of that. One install, one command, clean JSON out.

## MCP server

Use tteg directly from Claude Code, Cursor, or any MCP-compatible host from this repo:

```json
{
  "mcpServers": {
    "tteg": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/kiluazen/tteg", "tteg-mcp"]
    }
  }
}
```

You can also install the package once and run `tteg-mcp` locally.

Exposes:

- `search_images(query, count, orientation, width, height)`
- `save_image(url, output_path)`
- `search_and_save_image(query, output_path, index, orientation, width, height)`

No API key needed.

## Links

- [tteg.kushalsm.com](https://tteg.kushalsm.com) — landing page
- [PyPI](https://pypi.org/project/tteg/) — `pip install tteg`
- Free: 50 queries/day. No account needed.
