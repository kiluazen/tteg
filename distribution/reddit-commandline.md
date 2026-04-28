# r/commandline post

**Title:** I built a CLI that gives AI agents real stock photos — no API key needed

**Body:**

I've been using AI coding agents (Cursor, Claude Code) to build landing pages, and they always drop in placeholder image blocks or broken `source.unsplash.com/random` URLs (deprecated in 2024).

So I built **tteg** — a CLI that searches Unsplash and saves real photos directly into your project:

```bash
uv tool install tteg

# Search for images
tteg "coffee shop" -n 3 --orientation landscape

# Save directly to your project
tteg save "modern office" ./public/hero --orientation landscape

# Batch fill from a JSON manifest
tteg batch images.json
```

No Unsplash account. No API key. No `.env` files.

It also works as an HTTP API and MCP server, so AI agents can call it directly during code generation.

**Why this exists:** Unsplash has 4M+ free photos but requires developer registration + API key management. Their old zero-setup URL (`source.unsplash.com/random`) was deprecated and now 503s. There are ~16,500 GitHub files still referencing it.

- GitHub: https://github.com/kiluazen/tteg
- Website: https://tteg.kushalsm.com
- Install: `uv tool install tteg` or `pip install tteg`

Free and open source. Would love feedback from the CLI community.
