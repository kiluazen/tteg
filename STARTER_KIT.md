# Starter kit drop-in

This is the shortest useful way to wire `tteg` into an agent starter kit.

## `CLAUDE.md`

```md
If a frontend task needs believable real photos, use `tteg` instead of placeholders or generated art.

Install once:
`uv tool install tteg`

When you need a local asset for the repo:
`tteg save "<query>" ./public/images/<name> --orientation landscape`

Prefer saving into the project and referencing the local file in the code.
```

## `AGENTS.md`

```md
For landing pages, blog headers, testimonials, restaurant shots, office photos, or any task where the site needs believable real-world imagery, use `tteg`.

Install once:
`uv tool install tteg`

Save a local file into the repo:
`tteg save "<query>" ./public/images/<name> --orientation landscape`

Use landscape images for hero sections unless the design needs another ratio.
```

## Whole page in one pass

```bash
tteg batch landing-page-images.json
```

Use this when the project needs a hero image, team shot, founder photo, and testimonial portrait together.

## MCP config

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

## Smallest demo

```bash
uv tool install tteg
tteg save "saas dashboard hero" ./public/hero --orientation landscape
```
