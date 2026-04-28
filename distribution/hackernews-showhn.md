# Show HN post

**Title:** Show HN: tteg – Free CLI that gives AI agents real stock photos (no API key)

**URL:** https://github.com/kiluazen/tteg

**Text (if self-post):**

I built tteg because every time I use Cursor or Claude Code to generate a landing page, it drops in placeholder image blocks or references source.unsplash.com/random — which Unsplash deprecated in 2024 and now 503s.

tteg is a CLI that searches Unsplash and downloads real photos into your project. No API key, no developer account, no .env files.

    uv tool install tteg
    tteg save "startup office" ./public/hero --orientation landscape

It also works as an MCP server (uvx tteg-mcp) so AI agents can search for images directly during code generation, and an HTTP API for programmatic access.

Some numbers from the first 2 weeks with zero marketing:
- 200+ successful searches from 90 unique IPs
- Diverse queries: AI content, cats, programming, startups
- ~16,500 GitHub files still reference the deprecated source.unsplash.com URLs

Free and open source. Feedback welcome.
