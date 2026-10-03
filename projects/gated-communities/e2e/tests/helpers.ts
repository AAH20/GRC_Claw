import { test as base, expect, Page } from '@playwright/test';

/**
 * Shared test fixtures and helpers for Gated Communities E2E tests.
 */

export const TEST_USER = {
  email: 'test.admin@gated-communities.local',
  password: 'TestP@ssw0rd!2024',
  name: 'Test Admin',
};

export const TEST_TIER = {
  name: 'E2E Test Tier',
  level: 'bronze' as const,
  description: 'A tier created during E2E testing',
  benefits: ['Basic access', 'Community forums'],
  monthlyFee: 9.99,
};

export const TEST_MODERATION_CONTENT = {
  content: 'This is test content for moderation pipeline validation',
  contentType: 'post' as const,
};

export const TEST_COMMUNITY = {
  name: 'E2E Test Community',
  description: 'A community created during E2E testing',
  isPrivate: true,
};

/**
 * Authenticate a user and return the authenticated page.
 */
export async function authenticate(
  page: Page,
  email: string = TEST_USER.email,
  password: string = TEST_USER.password,
): Promise<void> {
  await page.goto('/auth/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: /sign in|log in/i }).click();
  await expect(page).toHaveURL(/\/dashboard|\/communities/, { timeout: 15_000 });
}

/**
 * Wait for the page to be fully loaded with network idle.
 */
export async function waitForPageReady(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle');
  await page.waitForLoadState('domcontentloaded');
}

/**
 * Safe click with retry logic for flaky UI elements.
 */
export async function safeClick(
  page: Page,
  selector: string,
  options: { timeout?: number; retries?: number } = {},
): Promise<void> {
  const { timeout = 10_000, retries = 3 } = options;
  let lastError: Error | undefined;

  for (let i = 0; i < retries; i++) {
    try {
      await page.locator(selector).click({ timeout });
      return;
    } catch (e) {
      lastError = e as Error;
      if (i < retries - 1) {
        await page.waitForTimeout(500 * (i + 1));
      }
    }
  }

  throw new Error(
    `Failed to click "${selector}" after ${retries} attempts: ${lastError?.message}`,
  );
}

/**
 * Assert that a toast/notification message appears with expected text.
 */
export async function expectToast(
  page: Page,
  messagePattern: RegExp | string,
): Promise<void> {
  const toast = page.locator('[data-testid="toast"], [role="alert"], .toast, .notification');
  await expect(toast).toBeVisible({ timeout: 10_000 });
  await expect(toast).toContainText(messagePattern);
}

/**
 * Generate a unique string for test data isolation.
 */
export function uniqueId(prefix = 'e2e'): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * API helper: make an authenticated request to the backend.
 */
export async function apiRequest(
  page: Page,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  path: string,
  body?: unknown,
): Promise<unknown> {
  const response = await page.request.fetch(`/api/v1${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    data: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok()) {
    const text = await response.text();
    throw new Error(
      `API ${method} /api/v1${path} failed: ${response.status()} ${response.statusText()} — ${text}`,
    );
  }

  return response.json();
}

export { base as test, expect };
