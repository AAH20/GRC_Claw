import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveURL(/.*login/);
    await expect(page.locator('h1')).toContainText('Login');
  });

  test('should display register page', async ({ page }) => {
    await page.goto('/register');
    await expect(page).toHaveURL(/.*register/);
    await expect(page.locator('h1')).toContainText('Register');
  });

  test('should show validation errors on empty login form', async ({ page }) => {
    await page.goto('/login');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Email is required')).toBeVisible();
    await expect(page.locator('text=Password is required')).toBeVisible();
  });

  test('should show validation errors on empty register form', async ({ page }) => {
    await page.goto('/register');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Name is required')).toBeVisible();
    await expect(page.locator('text=Email is required')).toBeVisible();
    await expect(page.locator('text=Password is required')).toBeVisible();
  });

  test('should navigate between login and register', async ({ page }) => {
    await page.goto('/login');
    await page.click('text=Register');
    await expect(page).toHaveURL(/.*register/);
    await page.click('text=Login');
    await expect(page).toHaveURL(/.*login/);
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*login/);
  });
});
