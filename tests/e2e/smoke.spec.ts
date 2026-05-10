import { test, expect } from '@playwright/test';

test('homepage renders correctly', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Lessons Hub/);
  await expect(page.locator('header nav')).toBeVisible();
  await expect(page.locator('a.site-title')).toHaveText('Lessons Hub');
});

test('navigation links are present', async ({ page }) => {
  await page.goto('/');
  const nav = page.locator('header nav ul');
  await expect(nav.locator('a[href*="/lessons/"]')).toBeVisible();
  await expect(nav.locator('a[href*="/repos/"]')).toBeVisible();
  await expect(nav.locator('a[href*="/tags/"]')).toBeVisible();
});

test('lessons page shows lesson cards', async ({ page }) => {
  await page.goto('/lessons/');
  const cards = page.locator('.lesson-card');
  await expect(cards.first()).toBeVisible();
  const count = await cards.count();
  expect(count).toBeGreaterThan(0);
});

test('repos page shows repo cards with descriptions', async ({ page }) => {
  await page.goto('/repos/');
  const cards = page.locator('.repo-card');
  await expect(cards.first()).toBeVisible();
  const descriptions = page.locator('.repo-card .description');
  const count = await descriptions.count();
  expect(count).toBeGreaterThan(0);
});

test('theme toggle works', async ({ page }) => {
  await page.goto('/');
  const html = page.locator('html');
  const toggle = page.locator('#theme-toggle');

  // Get initial theme
  const initial = await html.getAttribute('data-theme');
  expect(initial).toMatch(/^(light|dark)$/);

  // Click toggle
  await toggle.click();
  const toggled = await html.getAttribute('data-theme');
  expect(toggled).not.toBe(initial);

  // Click again to restore
  await toggle.click();
  const restored = await html.getAttribute('data-theme');
  expect(restored).toBe(initial);
});

test('search widget is present', async ({ page }) => {
  await page.goto('/lessons/');
  await expect(page.locator('#search')).toBeVisible();
});
