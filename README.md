# tteg

Free stock image search for AI coding agents. No API keys needed.

## Install

```bash
uv tool install tteg
```

## Usage

```bash
tteg "mountain sunset"
tteg "hero banner" -n 8 --orientation landscape
tteg "office workspace" --width 1920 --height 1080
```

Returns JSON with image URLs from Unsplash — ready for agents to drop into code.
