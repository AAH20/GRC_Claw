# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-flow.spec.ts >> Authentication Flow >> should show error for invalid registration data
- Location: tests/auth-flow.spec.ts:70:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByLabel('Name')

```

# Test source

```ts
  1   | import { test, expect, Page } from "@playwright/test";
  2   | 
  3   | /**
  4   |  * Authentication Flow E2E Tests
  5   |  *
  6   |  * Covers login, registration, logout, session persistence,
  7   |  * and route protection for the recruitment platform.
  8   |  */
  9   | 
  10  | const TEST_USER = {
  11  |   name: "E2E Test User",
  12  |   email: `e2e-test-${Date.now()}@example.com`,
  13  |   password: "TestPass123!",
  14  | };
  15  | 
  16  | async function registerUser(page: Page, user = TEST_USER): Promise<void> {
  17  |   await page.goto("/register");
  18  |   await page.getByLabel("Name").fill(user.name);
  19  |   await page.getByLabel("Email").fill(user.email);
  20  |   await page.getByLabel("Password").fill(user.password);
  21  |   await page.getByRole("button", { name: /sign up|register/i }).click();
  22  |   await expect(page).toHaveURL(/\/dashboard/);
  23  | }
  24  | 
  25  | async function loginUser(page: Page, user = TEST_USER): Promise<void> {
  26  |   await page.goto("/login");
  27  |   await page.getByLabel("Email").fill(user.email);
  28  |   await page.getByLabel("Password").fill(user.password);
  29  |   await page.getByRole("button", { name: /sign in|log in/i }).click();
  30  |   await expect(page).toHaveURL(/\/dashboard/);
  31  | }
  32  | 
  33  | test.describe("Authentication Flow", () => {
  34  |   test("should register a new user and redirect to dashboard", async ({ page }) => {
  35  |     await registerUser(page);
  36  | 
  37  |     // Verify user is on dashboard
  38  |     await expect(page.getByText(/welcome|dashboard/i).first()).toBeVisible();
  39  | 
  40  |     // Verify localStorage has token
  41  |     const token = await page.evaluate(() =>
  42  |       localStorage.getItem("recruitment_token")
  43  |     );
  44  |     expect(token).toBeTruthy();
  45  |   });
  46  | 
  47  |   test("should login with valid credentials", async ({ page }) => {
  48  |     // First register, then logout, then login
  49  |     await registerUser(page);
  50  |     await page.getByRole("button", { name: /logout|sign out/i }).click();
  51  |     await expect(page).toHaveURL(/\/login/);
  52  | 
  53  |     await loginUser(page);
  54  |     await expect(page.getByText(/welcome|dashboard/i).first()).toBeVisible();
  55  |   });
  56  | 
  57  |   test("should show error for invalid login credentials", async ({ page }) => {
  58  |     await page.goto("/login");
  59  |     await page.getByLabel("Email").fill("invalid@example.com");
  60  |     await page.getByLabel("Password").fill("wrongpassword");
  61  |     await page.getByRole("button", { name: /sign in|log in/i }).click();
  62  | 
  63  |     // Should show error message
  64  |     await expect(
  65  |       page.getByText(/invalid|error|incorrect|failed/i).first()
  66  |     ).toBeVisible();
  67  |     await expect(page).toHaveURL(/\/login/);
  68  |   });
  69  | 
  70  |   test("should show error for invalid registration data", async ({ page }) => {
  71  |     await page.goto("/register");
> 72  |     await page.getByLabel("Name").fill("");
      |                                   ^ Error: locator.fill: Test timeout of 30000ms exceeded.
  73  |     await page.getByLabel("Email").fill("not-an-email");
  74  |     await page.getByLabel("Password").fill("123");
  75  |     await page.getByRole("button", { name: /sign up|register/i }).click();
  76  | 
  77  |     // Should show validation errors
  78  |     await expect(
  79  |       page.getByText(/invalid|error|required|too short/i).first()
  80  |     ).toBeVisible();
  81  |   });
  82  | 
  83  |   test("should persist session across page reloads", async ({ page }) => {
  84  |     await registerUser(page);
  85  | 
  86  |     // Reload the page
  87  |     await page.reload();
  88  | 
  89  |     // Should still be authenticated
  90  |     await expect(page).toHaveURL(/\/dashboard/);
  91  |     await expect(page.getByText(/welcome|dashboard/i).first()).toBeVisible();
  92  |   });
  93  | 
  94  |   test("should logout and clear session", async ({ page }) => {
  95  |     await registerUser(page);
  96  | 
  97  |     await page.getByRole("button", { name: /logout|sign out/i }).click();
  98  |     await expect(page).toHaveURL(/\/login/);
  99  | 
  100 |     // Verify localStorage is cleared
  101 |     const token = await page.evaluate(() =>
  102 |       localStorage.getItem("recruitment_token")
  103 |     );
  104 |     expect(token).toBeNull();
  105 |   });
  106 | 
  107 |   test("should redirect unauthenticated users from protected routes", async ({
  108 |     page,
  109 |   }) => {
  110 |     // Clear any existing session
  111 |     await page.goto("/");
  112 |     await page.evaluate(() => {
  113 |       localStorage.removeItem("recruitment_token");
  114 |       localStorage.removeItem("recruitment_user");
  115 |     });
  116 | 
  117 |     // Try to access protected routes
  118 |     const protectedRoutes = [
  119 |       "/dashboard",
  120 |       "/candidates",
  121 |       "/jobs",
  122 |       "/interviews",
  123 |       "/analytics",
  124 |     ];
  125 | 
  126 |     for (const route of protectedRoutes) {
  127 |       await page.goto(route);
  128 |       await expect(page).toHaveURL(/\/login/);
  129 |     }
  130 |   });
  131 | 
  132 |   test("should redirect authenticated users away from login page", async ({
  133 |     page,
  134 |   }) => {
  135 |     await registerUser(page);
  136 | 
  137 |     // Try to access login page while authenticated
  138 |     await page.goto("/login");
  139 |     await expect(page).toHaveURL(/\/dashboard/);
  140 |   });
  141 | });
  142 | 
```