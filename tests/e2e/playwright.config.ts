import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  timeout: 5 * 60 * 1000, // 5 minutes per test
  use: {
    baseURL: process.env.TARGET_URL || 'https://lessons.johnboen.com',
    headless: true,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  reporter: [['list'], ['html', { open: 'never', outputFolder: '../../playwright-report' }]],
});
