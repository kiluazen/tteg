----
Show HN: tteg – Free stock image search for AI agents, no API key needed

https://github.com/kiluazen/tteg
----

Whenever I'm building with Claude Code or Cursor, the agent hits a wall the moment it needs a real image. Getting an Unsplash API key, registering an app, reading the docs — that's not something an agent can do mid-task.

So I built tteg: a CLI that wraps Unsplash, no auth required. I hold the keys server-side, you just search.

    uv tool install tteg
    tteg "mountain sunset"

Returns clean JSON — image URL, thumbnail, title:

    {
      "query": "mountain sunset",
      "results": [
        {
          "id": 1,
          "title": "Sunrise over Jamnik village",
          "image_url": "https://images.unsplash.com/...",
          "thumb_url": "https://images.unsplash.com/...&w=200"
        }
      ]
    }

Agents can pipe that straight into code. Supports orientation, width/height filtering, 1–10 results per query.

Free: 50 queries/day, no account needed.
https://tteg.kushalsm.com
https://pypi.org/project/tteg/
