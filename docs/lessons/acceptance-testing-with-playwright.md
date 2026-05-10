---
title: Acceptance Testing with Playwright
summary: Use BFS link crawling and smoke tests against live URLs to catch broken navigation and UI regressions before users do
date: 2026-05-10
phase: execution
lesson_type: process
status: active
tags: [testing, playwright, acceptance, crawling, ci, automation]
---

# Acceptance Testing with Playwright

## The Lesson

Browser-based acceptance tests that crawl your deployed site catch an entire class of bugs that unit tests and build-time validation cannot: broken links from content transformations, missing pages from routing errors, and UI regressions from CSS/JS interactions. A breadth-first link crawler plus targeted smoke tests gives high coverage with minimal test maintenance.

## Context

Lessons Hub is a static site built with Astro, deployed to GitHub Pages. It harvests markdown lessons from multiple source repositories, transforms relative links, and renders them as standalone pages. The build pipeline has 76 unit tests for harvesting logic and 138 backend tests for the RAG API — but none of these verify that the final rendered HTML actually works in a browser. Relative `.md` cross-references in source lessons get rewritten to internal routes during rendering; if the rewriter has a bug, the unit tests won't catch it because they don't exercise the full render path.

## What Happened

1. Playwright was added as a dev dependency with a config that targets any URL via the `TARGET_URL` environment variable, defaulting to the production site.
2. A BFS link crawler test was written: starting from `/`, it visits every internal page, extracts all `<a href>` links, queues unvisited internal links, and collects external links separately.
3. The first production run discovered **105 broken internal links** — all from lesson pages with relative `.md` cross-references that the existing link rewriter didn't handle.
4. The root cause was a rewriter that only recognized a specific filename pattern (`\d{3}_`) but source lessons used varied naming conventions. A general-case rewriter was added that resolves any `.md` link by slug matching against same-repo lessons.
5. After fixing, the crawl passed with zero broken links across 80+ pages.
6. Smoke tests were added for core UI: homepage title, navigation links, lesson cards, repo descriptions, theme toggle, and search widget presence.

## Key Insights

- **BFS crawl finds what static analysis misses.** Link validation at build time can check that a target file exists, but it can't verify that the routing layer, content transformation, and HTML rendering all agree. The crawler tests the final artifact as a user would experience it.

- **Track the source of each broken link.** The initial implementation used a flat URL queue, making it impossible to know which page linked to the broken URL. Changing the queue to `{ path, source }` tuples made error reports actionable: "404 at `/lessons/foo/` linked from `/lessons/bar/`".

- **Normalize URLs before deduplication.** Without normalization (stripping hashes, adding trailing slashes for non-file paths), the crawler visits the same page multiple times or misses pages entirely. The normalize function is small but load-bearing.

- **Soft-fail external links.** External sites may block HEAD requests, rate-limit, or be temporarily down. External link checks should warn but never fail the test suite, otherwise flaky third-party servers break your CI.

- **Environment-variable URL targeting enables reuse.** The same test suite runs against `localhost` during development, a preview deployment on PRs, and production after deploy. The only difference is `TARGET_URL`.

## Examples

### BFS Link Crawler (core algorithm)

```typescript
const visited = new Set<string>();
const queue: { path: string; source: string }[] = [{ path: '/', source: '(start)' }];
const errors: { url: string; status: number; linkedFrom: string }[] = [];

while (queue.length > 0) {
  const { path, source } = queue.shift()!;
  if (visited.has(path)) continue;
  visited.add(path);

  const response = await page.goto(path, { waitUntil: 'domcontentloaded' });
  if (response?.status() >= 400) {
    errors.push({ url: path, status: response.status(), linkedFrom: source });
    continue;
  }

  const hrefs = await page.locator('a[href]').evaluateAll(
    (links) => links.map((a) => a.getAttribute('href')).filter(Boolean)
  );

  for (const href of hrefs) {
    const normalized = normalize(href);
    if (normalized && !visited.has(normalized)) {
      queue.push({ path: normalized, source: path });
    }
  }
}

expect(errors).toHaveLength(0);
```

### Playwright Config (environment-variable targeting)

```typescript
export default defineConfig({
  timeout: 5 * 60 * 1000, // Crawl can visit 100+ pages
  use: {
    baseURL: process.env.TARGET_URL || 'https://lessons.johnboen.com',
    headless: true,
  },
});
```

### CI Integration (preview deploy then test)

```yaml
acceptance-tests:
  needs: deploy-preview
  steps:
    - uses: actions/checkout@v4
    - run: npm ci
    - run: npx playwright install chromium
    - run: npx playwright test
      env:
        TARGET_URL: ${{ needs.deploy-preview.outputs.preview-url }}
    - uses: actions/upload-artifact@v4
      if: failure()
      with:
        name: playwright-report
        path: playwright-report/
```

## Applicability

This pattern works for any static site or server-rendered application where:
- Content comes from external sources and undergoes transformation
- Routing is generated from data (dynamic routes, slug-based paths)
- Cross-references between pages exist in the source content
- Multiple deployment environments need the same validation

It is less useful for SPAs with client-side routing (the crawler won't trigger route transitions without additional scripting) or for sites behind authentication (requires session/cookie setup in the Playwright config).

## Related Lessons

- [Test Pyramid for Static Sites](test-pyramid-for-static-sites.md) — where acceptance tests fit in the overall testing strategy
- [Testing Cross-Repo Content Pipelines](testing-cross-repo-content-pipelines.md) — validating the content before it reaches the browser
- [Preflight Gates as Local CI](preflight-gates-as-local-ci.md) — running these tests locally before pushing
