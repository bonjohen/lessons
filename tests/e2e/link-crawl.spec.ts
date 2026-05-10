import { test, expect } from '@playwright/test';

test('all internal links resolve without 404s', async ({ page, baseURL }) => {
  const visited = new Set<string>();
  const queue: { path: string; source: string }[] = [{ path: '/', source: '(start)' }];
  const errors: { url: string; status: number; linkedFrom: string }[] = [];
  const externalLinks = new Set<string>();

  // Normalize URL to pathname only (strip origin, hash, trailing slash normalization)
  function normalize(href: string): string | null {
    try {
      const url = new URL(href, baseURL);
      // Skip non-http protocols
      if (!url.protocol.startsWith('http')) return null;
      // External link
      if (url.origin !== new URL(baseURL!).origin) {
        externalLinks.add(url.href);
        return null;
      }
      // Strip hash, normalize trailing slash
      let path = url.pathname;
      if (!path.endsWith('/') && !path.includes('.')) path += '/';
      return path;
    } catch {
      return null;
    }
  }

  while (queue.length > 0) {
    const { path, source } = queue.shift()!;
    if (visited.has(path)) continue;
    visited.add(path);

    const response = await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 30000 });
    const status = response?.status() ?? 0;

    if (status >= 400) {
      errors.push({ url: path, status, linkedFrom: source });
      continue;
    }

    // Collect all links on this page
    const hrefs = await page.locator('a[href]').evaluateAll((links) =>
      links.map((a) => a.getAttribute('href')).filter(Boolean) as string[]
    );

    for (const href of hrefs) {
      const normalized = normalize(href);
      if (normalized && !visited.has(normalized)) {
        queue.push({ path: normalized, source: path });
      }
    }
  }

  // Report results
  console.log(`\nCrawl complete: ${visited.size} pages visited`);
  console.log(`External links found: ${externalLinks.size}`);

  if (errors.length > 0) {
    console.log('\nBroken links:');
    for (const err of errors) {
      console.log(`  ${err.status} ${err.url} (linked from ${err.linkedFrom})`);
    }
  }

  expect(errors, `Found ${errors.length} broken internal link(s)`).toHaveLength(0);
});

test('external links are reachable', async ({ request, baseURL, page }) => {
  // First crawl to collect external links
  const visited = new Set<string>();
  const queue: string[] = ['/'];
  const externalLinks = new Set<string>();

  function normalize(href: string): string | null {
    try {
      const url = new URL(href, baseURL);
      if (!url.protocol.startsWith('http')) return null;
      if (url.origin !== new URL(baseURL!).origin) {
        externalLinks.add(url.href);
        return null;
      }
      let path = url.pathname;
      if (!path.endsWith('/') && !path.includes('.')) path += '/';
      return path;
    } catch {
      return null;
    }
  }

  // Quick crawl — just homepage + top-level nav pages to gather externals
  const seedPages = ['/', '/lessons/', '/repos/', '/tags/', '/about/'];
  for (const path of seedPages) {
    if (visited.has(path)) continue;
    visited.add(path);
    const response = await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 30000 });
    if (!response || response.status() >= 400) continue;
    const hrefs = await page.locator('a[href]').evaluateAll((links) =>
      links.map((a) => a.getAttribute('href')).filter(Boolean) as string[]
    );
    for (const href of hrefs) {
      normalize(href);
    }
  }

  // Check external links with HEAD (soft-fail: warn but don't break)
  const warnings: { url: string; status: number }[] = [];
  const checked = new Set<string>();

  for (const url of externalLinks) {
    if (checked.has(url)) continue;
    checked.add(url);
    try {
      const resp = await request.head(url, { timeout: 10000 });
      if (resp.status() >= 400) {
        warnings.push({ url, status: resp.status() });
      }
    } catch {
      warnings.push({ url, status: 0 });
    }
  }

  console.log(`\nExternal links checked: ${checked.size}`);
  if (warnings.length > 0) {
    console.log('Unreachable external links (warnings, not failures):');
    for (const w of warnings) {
      console.log(`  ${w.status || 'timeout'} ${w.url}`);
    }
  }

  // Soft-fail: log but don't assert (external sites may block HEAD requests)
  expect(true).toBe(true);
});
