# Reddit distribution posts for tteg

---

## r/ClaudeAI

**Title:** I made a free CLI so Claude Code can search stock images without needing an API key

Every time I use Claude Code to build anything with images, it either hallucinates placeholder URLs or stops to ask me for an Unsplash key. Both are annoying.

So I built `tteg` — a one-command image search that requires no setup:

```bash
uv tool install tteg
tteg "mountain sunset"
```

Returns clean JSON with real Unsplash URLs. Claude can use them directly. No key, no config, no rate limit headaches (I handle that server-side).

Free: 50 queries/day. Works with Claude Code, Cursor, or any agent that can run shell commands.

GitHub: https://github.com/kiluazen/tteg
PyPI: https://pypi.org/project/tteg/

---

## r/ChatGPTCoding

**Title:** Built a free image search CLI for AI coding assistants – no API keys, just JSON

When I'm using ChatGPT or any AI coding tool to build a site, finding real images mid-task always breaks the flow. Registering for Unsplash, copying API keys, adding them to .env files — it's friction that shouldn't exist.

I built `tteg` to fix that:

```bash
pip install tteg
tteg "hero banner" --orientation landscape
```

Returns JSON with image URLs, thumbnails, and titles. Your agent drops them straight into the code. No auth, no setup.

Supports up to 10 results, orientation filtering, and width/height targeting.

https://github.com/kiluazen/tteg | https://pypi.org/project/tteg/

---

## r/LocalLLaMA

**Title:** tteg – a free stock image search CLI for local agent workflows, no API key required

If you're running local agents (llama.cpp, Ollama, LM Studio, etc.) and building anything with images, you know the pain: you need real URLs but getting an Unsplash API key requires browser auth that your local agent can't do.

`tteg` is a thin CLI that proxies Unsplash. Install once, call from anywhere:

```bash
uv tool install tteg
tteg "office workspace" --width 1920 --height 1080 -n 3
```

Output is clean JSON — image URL, thumbnail, title. Pipe it into your agent's context and let it use real photos.

Works entirely from the terminal. I run the API on Cloud Run, so your local model doesn't need network creds.

Free: 50 queries/day. Source on GitHub: https://github.com/kiluazen/tteg
