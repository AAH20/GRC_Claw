# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-flow.spec.ts >> Authentication Flow >> should redirect authenticated users away from login page
- Location: tests/auth-flow.spec.ts:132:7

# Error details

```
Error: locator.fill: Error: strict mode violation: getByLabel('Password') resolved to 2 elements:
    1) <input value="" required="" id="password" type="password" placeholder="Min. 8 characters" class="block w-full rounded-lg border bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus:border-transparent border-gray-300 dark:border-gray-600 pl-10 pr-4 py-2.5 text-sm"/> aka getByRole('textbox', { name: 'Password', exact: true })
    2) <input value="" required="" type="password" id="confirm-password" placeholder="Confirm your password" class="block w-full rounded-lg border bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus:border-transparent border-gray-300 dark:border-gray-600 pl-10 pr-4 py-2.5 text-sm"/> aka getByRole('textbox', { name: 'Confirm Password' })

Call log:
  - waiting for getByLabel('Password')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - button "Open Next.js Dev Tools" [ref=e8] [cursor=pointer]
  - alert [ref=e12]
  - generic [ref=e14]:
    - generic [ref=e15]:
      - heading "Create Account" [level=3] [ref=e20]
      - paragraph [ref=e21]: Join RecruitHub to streamline your hiring
    - generic [ref=e22]:
      - generic [ref=e23]:
        - generic [ref=e24]:
          - generic [ref=e25]: Full Name
          - textbox "Full Name" [ref=e27]:
            - /placeholder: John Doe
            - text: E2E Test User
        - generic [ref=e28]:
          - generic [ref=e29]: Email
          - textbox "Email" [active] [ref=e31]:
            - /placeholder: you@company.com
            - text: e2e-test-1791024326251@example.com
        - generic [ref=e32]:
          - generic [ref=e33]: Password
          - textbox "Password" [ref=e35]:
            - /placeholder: Min. 8 characters
        - generic [ref=e36]:
          - generic [ref=e37]: Confirm Password
          - textbox "Confirm Password" [ref=e39]:
            - /placeholder: Confirm your password
        - button "Create Account" [ref=e40]
      - paragraph [ref=e41]:
        - text: Already have an account?
        - link "Sign in" [ref=e42] [cursor=pointer]:
          - /url: /login
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
> 20  |   await page.getByLabel("Password").fill(user.password);
      |                                     ^ Error: locator.fill: Error: strict mode violation: getByLabel('Password') resolved to 2 elements:
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
  72  |     await page.getByLabel("Name").fill("");
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
```