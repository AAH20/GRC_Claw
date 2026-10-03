import { test, expect, Page } from '@playwright/test';
import {
  TEST_USER,
  expectToast,
  safeClick,
  uniqueId,
  waitForPageReady,
} from './helpers';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure we start logged out
    await page.goto('/auth/login');
    await waitForPageReady(page);
  });

  test('should display login page', async ({ page }) => {
    await expect(page).toHaveURL(/\/auth\/login|\/login/);
    await expect(
      page.getByRole('heading', { name: /sign in|log in|login/i }),
    ).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(
      page.getByRole('button', { name: /sign in|log in|login/i }),
    ).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.getByLabel(/email/i).fill(TEST_USER.email);
    await page.getByLabel(/password/i).fill(TEST_USER.password);
    await page.getByRole('button', { name: /sign in|log in/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard|\/communities/, { timeout: 15_000 });
    await expect(
      page.getByText(/welcome|dashboard|communities/i),
    ).toBeVisible();
  });

  test('should reject login with invalid credentials', async ({ page }) => {
    await page.getByLabel(/email/i).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in|log in/i }).click();

    // Should show error message
    await expect(
      page.getByText(/invalid|incorrect|wrong|failed|error/i),
    ).toBeVisible({ timeout: 10_000 });

    // Should remain on login page
    await expect(page).toHaveURL(/\/auth\/login|\/login/);
  });

  test('should validate email format', async ({ page }) => {
    await page.getByLabel(/email/i).fill('not-an-email');
    await page.getByLabel(/password/i).fill('somepassword');
    await page.getByRole('button', { name: /sign in|log in/i }).click();

    // Should show email validation error
    await expect(
      page.getByText(/valid email|email.*invalid|invalid.*email/i),
    ).toBeVisible({ timeout: 5_000 });
  });

  test('should validate required fields on login', async ({ page }) => {
    // Try to submit empty form
    await page.getByRole('button', { name: /sign in|log in/i }).click();

    // Should show required field errors
    await expect(
      page.getByText(/email.*required|required.*email/i),
    ).toBeVisible({ timeout: 5_000 });
    await expect(
      page.getByText(/password.*required|required.*password/i),
    ).toBeVisible({ timeout: 5_000 });
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.getByLabel(/email/i).fill(TEST_USER.email);
    await page.getByLabel(/password/i).fill(TEST_USER.password);
    await page.getByRole('button', { name: /sign in|log in/i }).click();
    await expect(page).toHaveURL(/\/dashboard|\/communities/, { timeout: 15_000 });

    // Click logout
    await safeClick(page, '[data-testid="logout-button"], button:has-text("Logout"), button:has-text("Sign Out")');

    // Should redirect to login page
    await expect(page).toHaveURL(/\/auth\/login|\/login/, { timeout: 10_000 });
  });

  test('should protect authenticated routes', async ({ page }) => {
    // Try to access protected route without logging in
    await page.goto('/dashboard');
    await waitForPageReady(page);

    // Should redirect to login
    await expect(page).toHaveURL(/\/auth\/login|\/login/, { timeout: 10_000 });
  });

  test('should display registration page', async ({ page }) => {
    const registerLink = page.getByRole('link', {
      name: /sign up|register|create account/i,
    });

    if (await registerLink.isVisible({ timeout: 5_000 })) {
      await registerLink.click();
      await waitForPageReady(page);

      await expect(page).toHaveURL(/\/auth\/register|\/register/);
      await expect(
        page.getByRole('heading', { name: /sign up|register|create account/i }),
      ).toBeVisible();
    }
  });

  test('should register a new account', async ({ page }) => {
    const registerLink = page.getByRole('link', {
      name: /sign up|register|create account/i,
    });

    if (!(await registerLink.isVisible({ timeout: 5_000 }))) {
      test.skip('Registration link not available');
      return;
    }

    await registerLink.click();
    await waitForPageReady(page);

    const uniqueEmail = uniqueId('user') + '@gated-communities.local';

    await page.getByLabel(/name/i).fill('E2E Test User');
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill(TEST_USER.password);

    const confirmPassword = page.getByLabel(/confirm password|password confirmation/i);
    if (await confirmPassword.isVisible()) {
      await confirmPassword.fill(TEST_USER.password);
    }

    await page.getByRole('button', { name: /sign up|register|create account/i }).click();

    // Should redirect to dashboard or show success
    await expect(page).toHaveURL(/\/dashboard|\/communities|\/auth\/login/, {
      timeout: 15_000,
    });
  });

  test('should validate password match on registration', async ({ page }) => {
    const registerLink = page.getByRole('link', {
      name: /sign up|register|create account/i,
    });

    if (!(await registerLink.isVisible({ timeout: 5_000 }))) {
      test.skip('Registration link not available');
      return;
    }

    await registerLink.click();
    await waitForPageReady(page);

    await page.getByLabel(/name/i).fill('Test User');
    await page.getByLabel(/email/i).fill(uniqueId('user') + '@test.com');
    await page.getByLabel(/password/i).fill('Password123!');

    const confirmPassword = page.getByLabel(/confirm password|password confirmation/i);
    if (await confirmPassword.isVisible()) {
      await confirmPassword.fill('DifferentPassword456!');
    }

    await page.getByRole('button', { name: /sign up|register|create account/i }).click();

    // Should show password mismatch error
    await expect(
      page.getByText(/password.*match|match.*password|do not match/i),
    ).toBeVisible({ timeout: 5_000 });
  });

  test('should handle forgot password flow', async ({ page }) => {
    const forgotLink = page.getByRole('link', {
      name: /forgot password|reset password|forgot/i,
    });

    if (await forgotLink.isVisible({ timeout: 5_000 })) {
      await forgotLink.click();
      await waitForPageReady(page);

      await expect(
        page.getByRole('heading', { name: /forgot password|reset password/i }),
      ).toBeVisible();

      await page.getByLabel(/email/i).fill(TEST_USER.email);
      await page.getByRole('button', { name: /send|reset|submit/i }).click();

      await expectToast(page, /sent|emailed|reset link/i);
    }
  });

  test('should persist session across page refreshes', async ({ page }) => {
    // Login
    await page.getByLabel(/email/i).fill(TEST_USER.email);
    await page.getByLabel(/password/i).fill(TEST_USER.password);
    await page.getByRole('button', { name: /sign in|log in/i }).click();
    await expect(page).toHaveURL(/\/dashboard|\/communities/, { timeout: 15_000 });

    // Refresh the page
    await page.reload();
    await waitForPageReady(page);

    // Should still be on dashboard (session persisted)
    await expect(page).toHaveURL(/\/dashboard|\/communities/);
  });

  test('should handle session expiry gracefully', async ({ page }) => {
    // Login
    await page.getByLabel(/email/i).fill(TEST_USER.email);
    await page.getByLabel(/password/i).fill(TEST_USER.password);
    await page.getByRole('button', { name: /sign in|log in/i }).click();
    await expect(page).toHaveURL(/\/dashboard|\/communities/, { timeout: 15_000 });

    // Clear session storage to simulate expiry
    await page.evaluate(() => {
      sessionStorage.clear();
      localStorage.clear();
    });

    // Try to access protected route
    await page.goto('/dashboard');
    await waitForPageReady(page);

    // Should redirect to login
    await expect(page).toHaveURL(/\/auth\/login|\/login/, { timeout: 10_000 });
  });
});
