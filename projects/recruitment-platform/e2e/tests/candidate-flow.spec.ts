import { test, expect, Page } from "@playwright/test";

/**
 * Candidate Management Flow E2E Tests
 *
 * Covers candidate creation, listing, filtering, detail view,
 * status updates, and deletion.
 */

const TEST_CANDIDATE = {
  name: "Jane Smith",
  email: "jane.smith@example.com",
  phone: "+1-555-0123",
  skills: ["React", "TypeScript", "Node.js"],
  experience: 5,
  location: "San Francisco, CA",
  notes: "Strong frontend background",
};

async function loginAndNavigateToCandidates(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@example.com");
  await page.getByLabel("Password").fill("admin123");
  await page.getByRole("button", { name: /sign in|log in/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await page.getByRole("link", { name: /candidates/i }).click();
  await expect(page).toHaveURL(/\/candidates/);
}

async function createCandidate(page: Page, candidate = TEST_CANDIDATE): Promise<void> {
  await page.getByRole("button", { name: /add candidate|new candidate|create/i }).click();
  await page.getByLabel("Name").fill(candidate.name);
  await page.getByLabel("Email").fill(candidate.email);
  await page.getByLabel("Phone").fill(candidate.phone);
  await page.getByLabel("Location").fill(candidate.location);
  await page.getByLabel("Experience").fill(String(candidate.experience));
  await page.getByLabel("Notes").fill(candidate.notes || "");

  // Add skills
  for (const skill of candidate.skills) {
    await page.getByLabel("Skills").fill(skill);
    await page.getByRole("button", { name: /add skill/i }).click();
  }

  await page.getByRole("button", { name: /save|create|submit/i }).click();
}

test.describe("Candidate Management Flow", () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToCandidates(page);
  });

  test("should display candidates list page", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /candidates/i }).first()
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /add|new|create/i })).toBeVisible();
  });

  test("should create a new candidate", async ({ page }) => {
    await createCandidate(page);

    // Verify candidate appears in the list
    await expect(page.getByText(TEST_CANDIDATE.name)).toBeVisible();
    await expect(page.getByText(TEST_CANDIDATE.email)).toBeVisible();
  });

  test("should view candidate details", async ({ page }) => {
    await createCandidate(page);

    // Click on the candidate
    await page.getByText(TEST_CANDIDATE.name).click();

    // Verify detail view
    await expect(page.getByText(TEST_CANDIDATE.name)).toBeVisible();
    await expect(page.getByText(TEST_CANDIDATE.email)).toBeVisible();
    await expect(page.getByText(TEST_CANDIDATE.location)).toBeVisible();
    await expect(page.getByText(TEST_CANDIDATE.skills[0])).toBeVisible();
  });

  test("should filter candidates by status", async ({ page }) => {
    // Create a candidate first
    await createCandidate(page);

    // Use status filter
    await page.getByLabel("Status").selectOption("new");
    await expect(page.getByText(TEST_CANDIDATE.name)).toBeVisible();

    // Filter by a different status
    await page.getByLabel("Status").selectOption("hired");
    await expect(page.getByText(TEST_CANDIDATE.name)).not.toBeVisible();
  });

  test("should search candidates by name", async ({ page }) => {
    await createCandidate(page);

    // Search for the candidate
    await page.getByPlaceholder(/search/i).fill("Jane");
    await expect(page.getByText(TEST_CANDIDATE.name)).toBeVisible();

    // Search for something that doesn't exist
    await page.getByPlaceholder(/search/i).fill("NonExistentPerson12345");
    await expect(page.getByText(TEST_CANDIDATE.name)).not.toBeVisible();
  });

  test("should update candidate status", async ({ page }) => {
    await createCandidate(page);

    // Open candidate detail
    await page.getByText(TEST_CANDIDATE.name).click();

    // Update status
    await page.getByLabel("Status").selectOption("interview");
    await page.getByRole("button", { name: /save|update/i }).click();

    // Verify status change
    await expect(page.getByText(/interview/i)).toBeVisible();
  });

  test("should edit candidate information", async ({ page }) => {
    await createCandidate(page);

    // Open candidate detail
    await page.getByText(TEST_CANDIDATE.name).click();

    // Click edit
    await page.getByRole("button", { name: /edit/i }).click();

    // Update name
    await page.getByLabel("Name").fill("Jane Smith-Updated");
    await page.getByRole("button", { name: /save|update/i }).click();

    // Verify update
    await expect(page.getByText("Jane Smith-Updated")).toBeVisible();
  });

  test("should delete a candidate", async ({ page }) => {
    await createCandidate(page);

    // Open candidate detail
    await page.getByText(TEST_CANDIDATE.name).click();

    // Delete
    await page.getByRole("button", { name: /delete/i }).click();

    // Confirm deletion
    await page.getByRole("button", { name: /confirm|yes|delete/i }).click();

    // Verify candidate is removed
    await expect(page.getByText(TEST_CANDIDATE.name)).not.toBeVisible();
  });

  test("should show empty state when no candidates exist", async ({ page }) => {
    // Search for something that doesn't exist
    await page.getByPlaceholder(/search/i).fill("ZZZZNONEXISTENT");
    await expect(
      page.getByText(/no candidates|empty|not found/i).first()
    ).toBeVisible();
  });

  test("should validate required fields when creating candidate", async ({ page }) => {
    await page.getByRole("button", { name: /add candidate|new candidate|create/i }).click();

    // Try to submit without filling required fields
    await page.getByRole("button", { name: /save|create|submit/i }).click();

    // Should show validation errors
    await expect(
      page.getByText(/required|invalid|error/i).first()
    ).toBeVisible();
  });
});
