# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Authentication Flow >> should display login page
- Location: tests/auth.spec.ts:4:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "Login"
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" locator('h1') with timeout 5000ms
  - waiting for locator('h1')

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Authentication Flow', () => {
  4  |   test('should display login page', async ({ page }) => {
  5  |     await page.goto('/login');
  6  |     await expect(page).toHaveURL(/.*login/);
> 7  |     await expect(page.locator('h1')).toContainText('Login');
     |                                      ^ Error: expect(locator).toContainText(expected) failed
  8  |   });
  9  | 
  10 |   test('should display register page', async ({ page }) => {
  11 |     await page.goto('/register');
  12 |     await expect(page).toHaveURL(/.*register/);
  13 |     await expect(page.locator('h1')).toContainText('Register');
  14 |   });
  15 | 
  16 |   test('should show validation errors on empty login form', async ({ page }) => {
  17 |     await page.goto('/login');
  18 |     await page.click('button[type="submit"]');
  19 |     await expect(page.locator('text=Email is required')).toBeVisible();
  20 |     await expect(page.locator('text=Password is required')).toBeVisible();
  21 |   });
  22 | 
  23 |   test('should show validation errors on empty register form', async ({ page }) => {
  24 |     await page.goto('/register');
  25 |     await page.click('button[type="submit"]');
  26 |     await expect(page.locator('text=Name is required')).toBeVisible();
  27 |     await expect(page.locator('text=Email is required')).toBeVisible();
  28 |     await expect(page.locator('text=Password is required')).toBeVisible();
  29 |   });
  30 | 
  31 |   test('should navigate between login and register', async ({ page }) => {
  32 |     await page.goto('/login');
  33 |     await page.click('text=Register');
  34 |     await expect(page).toHaveURL(/.*register/);
  35 |     await page.click('text=Login');
  36 |     await expect(page).toHaveURL(/.*login/);
  37 |   });
  38 | 
  39 |   test('should redirect unauthenticated users to login', async ({ page }) => {
  40 |     await page.goto('/dashboard');
  41 |     await expect(page).toHaveURL(/.*login/);
  42 |   });
  43 | });
  44 | 
```