import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Playwright E2E Test Configuration
 *
 * Tests the Gated Communities platform end-to-end across multiple browsers.
 * Assumes the frontend dev server is running on localhost:3000 and the
 * FastAPI backend is running on localhost:8000.
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    expect: {
      timeout: 10_000,
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 7'] },
    },
  ],
  webServer: [
    {
      command: 'npm run dev',
      cwd: path.resolve(__dirname, '../frontend'),
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: 'uvicorn gated_communities.main:app --host 0.0.0.0 --port 8000',
      cwd: path.resolve(__dirname, '..'),
      url: 'http://localhost:8000/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
