import { test, expect, Page } from "@playwright/test";

/**
 * Interview Scheduling Flow E2E Tests
 *
 * Covers interview creation, scheduling, calendar view,
 * status updates, and feedback submission.
 */

const TEST_INTERVIEW = {
  candidateName: "Jane Smith",
  jobTitle: "Senior Frontend Engineer",
  type: "technical" as const,
  date: "2026-10-15",
  time: "10:00",
  duration: 60,
  interviewers: ["John Manager", "Sarah Lead"],
  location: "Video Call",
  notes: "Focus on React and system design",
};

async function loginAndNavigateToInterviews(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@example.com");
  await page.getByLabel("Password").fill("admin123");
  await page.getByRole("button", { name: /sign in|log in/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await page.getByRole("link", { name: /interviews/i }).click();
  await expect(page).toHaveURL(/\/interviews/);
}

async function scheduleInterview(page: Page, interview = TEST_INTERVIEW): Promise<void> {
  await page.getByRole("button", { name: /schedule|create|new interview|add/i }).click();
  await page.getByLabel("Candidate").fill(interview.candidateName);
  await page.getByLabel("Job").fill(interview.jobTitle);
  await page.getByLabel("Type").selectOption(interview.type);
  await page.getByLabel("Date").fill(interview.date);
  await page.getByLabel("Time").fill(interview.time);
  await page.getByLabel("Duration").fill(String(interview.duration));
  await page.getByLabel("Location").fill(interview.location);
  await page.getByLabel("Notes").fill(interview.notes || "");

  // Add interviewers
  for (const interviewer of interview.interviewers) {
    await page.getByLabel("Interviewers").fill(interviewer);
    await page.getByRole("button", { name: /add interviewer/i }).click();
  }

  await page.getByRole("button", { name: /save|schedule|create|submit/i }).click();
}

test.describe("Interview Scheduling Flow", () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToInterviews(page);
  });

  test("should display interviews list page", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /interviews/i }).first()
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /schedule|create|new|add/i })
    ).toBeVisible();
  });

  test("should schedule a new interview", async ({ page }) => {
    await scheduleInterview(page);

    // Verify interview appears in the list
    await expect(page.getByText(TEST_INTERVIEW.candidateName)).toBeVisible();
    await expect(page.getByText(TEST_INTERVIEW.jobTitle)).toBeVisible();
  });

  test("should view interview details", async ({ page }) => {
    await scheduleInterview(page);

    // Click on the interview
    await page.getByText(TEST_INTERVIEW.candidateName).click();

    // Verify detail view
    await expect(page.getByText(TEST_INTERVIEW.candidateName)).toBeVisible();
    await expect(page.getByText(TEST_INTERVIEW.jobTitle)).toBeVisible();
    await expect(page.getByText(TEST_INTERVIEW.location)).toBeVisible();
  });

  test("should filter interviews by status", async ({ page }) => {
    await scheduleInterview(page);

    // Filter by scheduled status
    await page.getByLabel("Status").selectOption("scheduled");
    await expect(page.getByText(TEST_INTERVIEW.candidateName)).toBeVisible();

    // Filter by completed status
    await page.getByLabel("Status").selectOption("completed");
    await expect(page.getByText(TEST_INTERVIEW.candidateName)).not.toBeVisible();
  });

  test("should filter interviews by type", async ({ page }) => {
    await scheduleInterview(page);

    // Filter by technical type
    await page.getByLabel("Type").selectOption("technical");
    await expect(page.getByText(TEST_INTERVIEW.candidateName)).toBeVisible();

    // Filter by behavioral type
    await page.getByLabel("Type").selectOption("behavioral");
    await expect(page.getByText(TEST_INTERVIEW.candidateName)).not.toBeVisible();
  });

  test("should update interview status to completed", async ({ page }) => {
    await scheduleInterview(page);

    // Open interview detail
    await page.getByText(TEST_INTERVIEW.candidateName).click();

    // Update status
    await page.getByLabel("Status").selectOption("completed");
    await page.getByRole("button", { name: /save|update/i }).click();

    // Verify status change
    await expect(page.getByText(/completed/i)).toBeVisible();
  });

  test("should cancel an interview", async ({ page }) => {
    await scheduleInterview(page);

    // Open interview detail
    await page.getByText(TEST_INTERVIEW.candidateName).click();

    // Cancel
    await page.getByRole("button", { name: /cancel/i }).click();

    // Confirm cancellation
    await page.getByRole("button", { name: /confirm|yes|cancel/i }).click();

    // Verify status change
    await expect(page.getByText(/cancelled/i)).toBeVisible();
  });

  test("should add interview feedback", async ({ page }) => {
    await scheduleInterview(page);

    // Open interview detail
    await page.getByText(TEST_INTERVIEW.candidateName).click();

    // Mark as completed first
    await page.getByLabel("Status").selectOption("completed");
    await page.getByRole("button", { name: /save|update/i }).click();

    // Add feedback
    await page.getByLabel("Feedback").fill("Strong technical skills, good culture fit.");
    await page.getByRole("button", { name: /save feedback|submit feedback/i }).click();

    // Verify feedback is saved
    await expect(page.getByText("Strong technical skills")).toBeVisible();
  });

  test("should edit interview details", async ({ page }) => {
    await scheduleInterview(page);

    // Open interview detail
    await page.getByText(TEST_INTERVIEW.candidateName).click();

    // Click edit
    await page.getByRole("button", { name: /edit/i }).click();

    // Update time
    await page.getByLabel("Time").fill("14:00");
    await page.getByRole("button", { name: /save|update/i }).click();

    // Verify update
    await expect(page.getByText("14:00")).toBeVisible();
  });

  test("should delete an interview", async ({ page }) => {
    await scheduleInterview(page);

    // Open interview detail
    await page.getByText(TEST_INTERVIEW.candidateName).click();

    // Delete
    await page.getByRole("button", { name: /delete/i }).click();

    // Confirm deletion
    await page.getByRole("button", { name: /confirm|yes|delete/i }).click();

    // Verify interview is removed
    await expect(page.getByText(TEST_INTERVIEW.candidateName)).not.toBeVisible();
  });

  test("should show calendar view", async ({ page }) => {
    await scheduleInterview(page);

    // Switch to calendar view
    await page.getByRole("button", { name: /calendar/i }).click();

    // Verify calendar is displayed
    await expect(page.getByText(/calendar|month|week|day/i).first()).toBeVisible();
  });

  test("should validate required fields when scheduling interview", async ({
    page,
  }) => {
    await page.getByRole("button", { name: /schedule|create|new interview|add/i }).click();

    // Try to submit without filling required fields
    await page.getByRole("button", { name: /save|schedule|create|submit/i }).click();

    // Should show validation errors
    await expect(
      page.getByText(/required|invalid|error/i).first()
    ).toBeVisible();
  });
});
