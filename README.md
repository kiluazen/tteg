# tteg

Free stock image search CLI for AI coding agents. No API keys, no setup.

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

## Why

Agents frequently need real images — hero banners, product shots, blog headers. The normal path (register for Unsplash, get an API key, handle rate limits) is too much friction for a mid-task agent call.

`tteg` abstracts all of that. One install, one command, clean JSON out.

## Links

- [tteg.kushalsm.com](https://tteg.kushalsm.com) — landing page
- [PyPI](https://pypi.org/project/tteg/) — `pip install tteg`
- Free: 50 queries/day. No account needed.
