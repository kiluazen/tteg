# r/SideProject post

**Title:** tteg — free CLI that fixes placeholder images in AI-generated landing pages

**Body:**

**Problem:** Every time an AI agent (Cursor, Claude Code, Copilot) generates a landing page, it drops in placeholder image blocks or dead `source.unsplash.com/random` URLs. You end up manually finding and downloading stock photos.

**Solution:** tteg — a free CLI that searches Unsplash and saves real photos into your project. Zero setup, no API key needed.

```bash
uv tool install tteg
tteg save "startup team meeting" ./public/hero --orientation landscape
# → saves a real Unsplash photo to ./public/hero.jpg
```

**What it does:**
- `tteg search` — returns image URLs (great for piping into scripts)
- `tteg save` — downloads a photo directly into your project
- `tteg batch` — fills multiple images from a JSON manifest (one command for an entire landing page)
- HTTP API + MCP server — AI agents can call it directly during code generation

**Traction so far:**
- 200+ successful searches from 90 unique IPs in the first 2 weeks
- Zero marketing — all organic from GitHub/PyPI discovery
- 16,500+ GitHub files still reference the deprecated source.unsplash.com URLs, so there's real demand

**Stack:** Python CLI + FastAPI on Google Cloud Run + Unsplash API (with Pexels fallback)

Free and open source: https://github.com/kiluazen/tteg
Website: https://tteg.kushalsm.com

Would love to hear what you think. Any feedback welcome.
