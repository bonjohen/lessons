---
title: "Base URL Misconfiguration Breaks Subdirectory Deploys"
summary: "When deploying a static site to a subdirectory path (e.g., `github.io/project/` instead of a custom domain root), every internal link must be prefixed with the base path. Setting the framework's `site` config is not enough — you must also set `base`, and every hardcoded absolute `href` in components..."
date: 2026-05-13
lesson_type: deployment
tags: [security, deployment, astro, ai]
---
# Base URL Misconfiguration Breaks Subdirectory Deploys

## The Lesson

When deploying a static site to a subdirectory path (e.g., `github.io/project/` instead of a custom domain root), every internal link must be prefixed with the base path. Setting the framework's `site` config is not enough — you must also set `base`, and every hardcoded absolute `href` in components and pages must use the base prefix. This is always more files than you expect.

## Context

An Astro static site was deployed to GitHub Pages at `bonjohen.github.io/morelessons/`. The Astro config had `site: 'https://bonjohen.github.io/morelessons'` but no `base` property. The site had 10 files containing hardcoded root-relative links (`/lessons/`, `/tags/`, `/categories/`, `/ask/`), plus Pagefind search assets loaded from `/pagefind/`. The build succeeded, CI deployed successfully, and the homepage loaded — but every link on the site returned a 404.

## What Happened

1. The site was developed with `npm run dev` on `localhost:4321`, where all root-relative links worked because there was no subdirectory prefix.
2. The first deployment to GitHub Pages succeeded (build green, deploy green). The homepage rendered correctly because `index.html` was served at the repo's Pages root.
3. Clicking any link navigated to `bonjohen.github.io/lessons/` instead of `bonjohen.github.io/morelessons/lessons/` — 404 on every navigation.
4. The fix required two changes: (a) add `base: '/morelessons'` to `astro.config.mjs` and correct `site` to `'https://bonjohen.github.io'`, and (b) replace every hardcoded `href="/..."` with `` href={`${base}/...`} `` using `import.meta.env.BASE_URL`.
5. The fix touched 10 files: 1 config file, 5 components, and 4 pages. Every component that generated any link needed the prefix — nav links, lesson cards, tag chips, category links, search asset paths.
6. An initial attempt to strip the trailing slash from `BASE_URL` using a regex (`/\/$/`) caused an esbuild parse error in one component (BaseLayout.astro) due to interaction with inline `<script>` blocks. Switching to `.endsWith('/')` + `.slice(0, -1)` resolved it.

## Key Insights

- **`site` and `base` are different configs with different effects.** In Astro, `site` sets the canonical URL for sitemap/SEO. `base` prefixes all generated paths. Setting `site` to a subdirectory URL does NOT automatically prefix links — you must set `base` separately. Other frameworks (Next.js `basePath`, Vite `base`) have the same split.
- **Root-relative links are a subdirectory deployment anti-pattern.** During development, `/lessons/` and `${base}/lessons/` behave identically because `base` is `/`. This means the bug is invisible until the first subdirectory deploy. The safe default is to always use the base prefix from day one, even if you think you'll deploy to a root domain.
- **The blast radius is always larger than expected.** You might think "just update the nav links" — but every component that generates any `href` or asset `src` needs the prefix. In this case: BaseLayout nav (5 links), LessonCard (2 links), TagList (1 link), MetadataPanel (1 link), SearchBox (2 asset paths), plus 4 page files with tag/category links.
- **Regex in Astro frontmatter can break esbuild.** Astro's frontmatter is processed by esbuild, which can misparse regex literals containing `/` near inline scripts. Use string methods (`.endsWith()`, `.slice()`) instead of regex (`.replace(/\/$/, '')`) in component frontmatter to avoid parser ambiguity.

## Examples

**Astro config — before:**
```js
export default defineConfig({
  site: 'https://bonjohen.github.io/morelessons',
});
```

**Astro config — after:**
```js
export default defineConfig({
  site: 'https://bonjohen.github.io',
  base: '/morelessons',
});
```

**Component link — before:**
```astro
<a href={`/lessons/${lesson.slug}/`}>{lesson.title}</a>
```

**Component link — after:**
```astro
---
const base = import.meta.env.BASE_URL.endsWith('/')
  ? import.meta.env.BASE_URL.slice(0, -1)
  : import.meta.env.BASE_URL;
---
<a href={`${base}/lessons/${lesson.slug}/`}>{lesson.title}</a>
```

## Applicability

This applies to any static site framework deployed to a URL subdirectory: GitHub Pages project sites, GitLab Pages, any reverse-proxy path prefix. It does NOT apply to custom domain deployments where the site is served from the domain root — in that case, root-relative links work fine and `base` should be `/` or omitted.

## Related Lessons

- [XSS via innerHTML in LLM Chat Interfaces](xss-in-llm-chat-interfaces.md) — discovered in the same deploy cycle
- [Enable GitHub Pages Before First Deploy](enable-pages-before-first-deploy.md) — the other first-deploy failure in this project
