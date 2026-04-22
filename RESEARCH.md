# 16,500+ GitHub files still hotlink a deprecated Unsplash endpoint

_Published: 2026-04-21. Data collected via GitHub's authenticated code-search API._

## Summary

Unsplash deprecated the `source.unsplash.com/random` endpoint in mid-2024. The endpoint has been returning `503 Service Unavailable` for over a year and is never coming back. An authenticated code-search across GitHub returns approximately **16,500 file hits** that still reference it today, across hundreds of unique repositories — including several well-known open-source projects currently shipping broken `<img>` tags to their users.

| Language filter | File hits |
|---|---:|
| JavaScript | 7,856 |
| HTML | 6,016 |
| TypeScript | 1,444 |
| Vue | 1,012 |
| Svelte | 114 |
| Astro | 105 |
| **Total** | **≈ 16,547** |

(The search is repo-level deduped to ~885 unique repositories after filtering to stars ≥ 5, non-archived, issues enabled, pushed in the last 12 months.)

## Notable repos currently shipping broken images

Ranked by `stars × recency`. Each entry links to the exact affected file + line at a pinned commit SHA:

| # | Repo | Stars | File | Line |
|---|---|---:|---|---:|
| 1 | [nuxt/website-v2](https://github.com/nuxt/website-v2) | 2,252 | `components/molecules/cards/ContentCardTemplate.vue` | L79 |
| 2 | [guocaoyi/create-chrome-ext](https://github.com/guocaoyi/create-chrome-ext) | 2,116 | `template-vue-js/src/newtab/NewTab.vue` | L65 |
| 3 | [debridmediamanager/debrid-media-manager](https://github.com/debridmediamanager/debrid-media-manager) | 1,266 | `src/pages/api/info/movie.ts` | L85, L96 |
| 4 | [fspecii/ace-step-ui](https://github.com/fspecii/ace-step-ui) | 991 | `App.tsx` | — |
| 5 | [umaranis/svelte-lexical](https://github.com/umaranis/svelte-lexical) | 581 | `packages/svelte-lexical/src/lib/components/toolbar/dialogs/InsertImageUriDialogBody.svelte` | L23 (placeholder-only) |
| 6 | [gravitano/nuxt3-tailwind-kit](https://github.com/gravitano/nuxt3-tailwind-kit) | 291 | `layers/blog/pages/blog/posts/[id].vue` | L44 |
| 7 | [ilhammeidi/veluxi-starter](https://github.com/ilhammeidi/veluxi-starter) | 112 | `components/Blog/Blog.vue` | — |
| 8 | [samchen08/vtj.pro](https://github.com/samchen08/vtj.pro) | 62 | `docs/src/examples/ui/action/action-6.vue` | — |
| 9 | [Teknasyon/rocket-ui](https://github.com/Teknasyon/rocket-ui) | 40 | `src/components/Avatar/RAvatar.vue` | — |
| 10 | [nent/nent](https://github.com/nent/nent) | 28 | `tools/docs/src/pages/routing/dynamic/child.html` | L5 |
| 11 | [andrewh0/okcss](https://github.com/andrewh0/okcss) | 29 | `demo.html` | L187, L196 |
| 12 | [varya/varya.github.com](https://github.com/varya/varya.github.com) | 10 | `src/components/Hero/Hero.stories.js` | L26, L32 |
| 13 | [antoinebou12/DasherControl](https://github.com/antoinebou12/DasherControl) | 7 | `frontend/components/applets/Shortcut/Shortcut.vue` | L26 |

The full search output (paginated dumps plus per-repo metadata fetched via GraphQL) lived in `/tmp/unsplash_search/` during collection.

## Why this happened

The `source.unsplash.com/random` endpoint used to be the zero-setup way to get "a random Unsplash photo" without signing up for an API key. It made its way into every boilerplate, tutorial, and AI-coding demo on the internet. When Unsplash shut it down in mid-2024, all of that code quietly broke — templates kept getting forked, agents kept emitting the same snippet they'd memorized from training data, and nobody's CI catches a `<img>` that 503s.

## A related, newer symptom: AI-coded landing pages

The pattern is now self-reinforcing. AI coding agents (Claude Code, Cursor, Codex, Windsurf, et al.) frequently emit exactly the same dead URL when they're building a landing page, blog, or demo — because it appeared thousands of times in the training data as the "right answer." The user ships, the deploy looks fine in review, and then every `<img>` tile on the live site is gray.

## Mitigations

1. **Pin specific Unsplash photo URLs.** The `images.unsplash.com/photo-<id>?w=...&h=...&fit=crop&q=80` pattern still works indefinitely. Pick photos manually, pin them, move on.

2. **Self-host the assets.** Download once, commit the JPG, use a local path. Fastest to load, no third-party dependency at runtime.

3. **Resolve real images at build time.** If an AI agent is going to build the page, the agent can also fetch a real photo and commit it. This is the fix that works at agent scale, and it is why I built **[tteg](https://github.com/kiluazen/tteg)** — a CLI + HTTP API + MCP server that gives agents real Unsplash photos with zero setup (no API key, no developer account). One call:

   ```bash
   uv tool install tteg
   tteg save "modern office" ./public/hero --orientation landscape
   ```

   The tool writes a real `.jpg` into the repo. An MCP server is included for Claude Code / Cursor / Windsurf. Landing: <https://tteg.kushalsm.com>.

4. **Add a linter rule.** Any repo that regenerates or re-skins a site via an AI agent should fail its build if `source.unsplash.com` shows up in `public/` or `src/`. This is two lines in a pre-commit hook.

## Reproducing the search

```sh
curl -H "Authorization: Bearer $(gh auth token)" \
     -H "Accept: application/vnd.github+json" \
  "https://api.github.com/search/code?q=%22source.unsplash.com%2Frandom%22+language:HTML&per_page=100"
```

Repeat for `language:JavaScript`, `TypeScript`, `Vue`, `Svelte`, `Astro`. Code search is authenticated-only and capped at 10 RPS per token, so plan accordingly.

## Practical action for maintainers

If you are shipping a template, starter, or live site, run:

```sh
grep -RIn "source.unsplash.com/random" .
```

If you get a hit, every user of your repo is looking at a broken image tile right now. The fix is two minutes.

— Kushal (`@kiluazen` on GitHub) · `kushal@kushalsm.com`
