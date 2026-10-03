import { test, expect, Page } from "@playwright/test";

/**
 * Authentication Flow E2E Tests
 *
 * Covers login, registration, logout, session persistence,
 * and route protection for the recruitment platform.
 */

const TEST_USER = {
  name: "E2E Test User",
  email: `e2e-test-${Date.now()}@example.com`,
  password: "TestPass123!",
};

async function registerUser(page: Page, user = TEST_USER): Promise<void> {
  await page.goto("/register");
  await page.getByLabel("Name").fill(user.name);
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password", { exact: true }).fill(user.password);
  await page.getByRole("button", { name: /sign up|register/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

async function loginUser(page: Page, user = TEST_USER): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);
  await page.getByRole("button", { name: /sign in|log in/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

test.describe("Authentication Flow", () => {
  test("should register a new user and redirect to dashboard", async ({ page }) => {
    await registerUser(page);

    // Verify user is on dashboard
    await expect(page.getByText(/welcome|dashboard/i).first()).toBeVisible();

    // Verify localStorage has token
    const token = await page.evaluate(() =>
      localStorage.getItem("recruitment_token")
    );
    expect(token).toBeTruthy();
  });

  test("should login with valid credentials", async ({ page }) => {
    // First register, then logout, then login
    await registerUser(page);
    await page.getByRole("button", { name: /logout|sign out/i }).click();
    await expect(page).toHaveURL(/\/login/);

    await loginUser(page);
    await expect(page.getByText(/welcome|dashboard/i).first()).toBeVisible();
  });

  test("should show error for invalid login credentials", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("invalid@example.com");
    await page.getByLabel("Password").fill("wrongpassword");
    await page.getByRole("button", { name: /sign in|log in/i }).click();

    // Should show error message
    await expect(
      page.getByText(/invalid|error|incorrect|failed/i).first()
    ).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("should show error for invalid registration data", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel("Name").fill("");
    await page.getByLabel("Email").fill("not-an-email");
    await page.getByLabel("Password").fill("123");
    await page.getByRole("button", { name: /sign up|register/i }).click();

    // Should show validation errors
    await expect(
      page.getByText(/invalid|error|required|too short/i).first()
    ).toBeVisible();
  });

  test("should persist session across page reloads", async ({ page }) => {
    await registerUser(page);

    // Reload the page
    await page.reload();

    // Should still be authenticated
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText(/welcome|dashboard/i).first()).toBeVisible();
  });

  test("should logout and clear session", async ({ page }) => {
    await registerUser(page);

    await page.getByRole("button", { name: /logout|sign out/i }).click();
    await expect(page).toHaveURL(/\/login/);

    // Verify localStorage is cleared
    const token = await page.evaluate(() =>
      localStorage.getItem("recruitment_token")
    );
    expect(token).toBeNull();
  });

  test("should redirect unauthenticated users from protected routes", async ({
    page,
  }) => {
    // Clear any existing session
    await page.goto("/");
    await page.evaluate(() => {
      localStorage.removeItem("recruitment_token");
      localStorage.removeItem("recruitment_user");
    });

    // Try to access protected routes
    const protectedRoutes = [
      "/dashboard",
      "/candidates",
      "/jobs",
      "/interviews",
      "/analytics",
    ];

    for (const route of protectedRoutes) {
      await page.goto(route);
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test("should redirect authenticated users away from login page", async ({
    page,
  }) => {
    await registerUser(page);

    // Try to access login page while authenticated
    await page.goto("/login");
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
