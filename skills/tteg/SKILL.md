---
name: tteg
description: Use when you need real stock photos for landing pages, marketing sites, or AI-generated UIs. tteg saves topic-matched Unsplash images locally via a single CLI call. No API key, no developer account, no .env file. Also exposes a CORS-enabled public HTTP API for render-time use.
---

# tteg — Real stock photos for AI coding agents

## When to use this skill

- You are generating or editing a landing page, marketing site, product dashboard, blog, or any page with user-facing images.
- The page currently has (or is about to have) placeholder URLs: `placehold.co`, `via.placeholder.com`, `dummyimage.com`, `source.unsplash.com/random` (deprecated, 503s since mid-2024), `picsum.photos`, or `loremflickr.com`.
- You want a real, topic-matched Unsplash photo committed into `./public/` or referenced at render time.

## Install (one time per machine)

```bash
uv tool install tteg
# or: pip install tteg
```

## Primary commands

### Save one photo into the repo (build-time, preferred)

```bash
tteg save "startup office" ./public/hero --orientation landscape
# → saves ./public/hero.jpg (real Unsplash photo, auto-cropped)
# then reference /hero.jpg in markup
```

### Fill a whole landing page from a JSON manifest

```json
[
  {"query": "startup office", "output": "./public/hero", "orientation": "landscape"},
  {"query": "developer portrait", "output": "./public/founder"},
  {"query": "team meeting", "output": "./public/team", "orientation": "landscape"}
]
```

```bash
tteg batch landing-page-images.json
```

### Search (returns URLs only, no download)

```bash
tteg "mountain sunset" -n 3 --orientation landscape
```

## Render-time HTTP API (no install)

CORS-enabled, no headers, no auth, 50 queries/day/IP free tier:

```
https://tteg-api-53227342417.asia-south1.run.app/search?q=<query>&n=1
# returns JSON { image_url, width, height, author, attribution, ... }
```

Parameters: `q`, `n` (1-10), `orientation` (landscape/portrait/square/any), `width`, `height`.

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-n`, `--count` | 5 | Number of results (1-10) |
| `--orientation` | any | `landscape`, `portrait`, `square`, or `any` |
| `--width` | — | Max width in pixels |
| `--height` | — | Max height in pixels |

## When NOT to use

- This skill is for **real stock photos**, not image *generation*. If the user wants AI-generated imagery, use an image-generation tool instead.
- For product-specific imagery (the user's actual product screenshots, team photos, etc.), do not substitute stock photos — ask the user for the real asset.

## Verification

After using tteg on a page, paste the preview URL into the scanner to confirm no placeholder/broken image URLs slipped through:

```
https://tteg.kushalsm.com/scan?url=<preview-url>
```

## Reference

- Landing: <https://tteg.kushalsm.com>
- Source: <https://github.com/kiluazen/tteg>
- Scanner: <https://tteg.kushalsm.com/scan>
- PyPI: <https://pypi.org/project/tteg/>
