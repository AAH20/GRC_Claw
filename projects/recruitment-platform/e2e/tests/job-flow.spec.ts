import { test, expect, Page } from "@playwright/test";

/**
 * Job Posting and Application Flow E2E Tests
 *
 * Covers job creation, listing, detail view, application submission,
 * and job status management.
 */

const TEST_JOB = {
  title: "Senior Frontend Engineer",
  department: "Engineering",
  location: "Remote",
  type: "full-time" as const,
  salaryMin: 120000,
  salaryMax: 180000,
  description:
    "We are looking for a Senior Frontend Engineer to join our team. You will be responsible for building user interfaces using React and TypeScript.",
  requirements: ["React", "TypeScript", "Node.js", "GraphQL"],
  status: "open" as const,
};

const TEST_APPLICATION = {
  candidateName: "John Doe",
  candidateEmail: "john.doe@example.com",
  coverLetter: "I am very interested in this position...",
};

async function loginAndNavigateToJobs(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@example.com");
  await page.getByLabel("Password").fill("admin123");
  await page.getByRole("button", { name: /sign in|log in/i }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await page.getByRole("link", { name: /jobs|positions/i }).click();
  await expect(page).toHaveURL(/\/jobs/);
}

async function createJob(page: Page, job = TEST_JOB): Promise<void> {
  await page.getByRole("button", { name: /post job|new job|create job|add/i }).click();
  await page.getByLabel("Title").fill(job.title);
  await page.getByLabel("Department").fill(job.department);
  await page.getByLabel("Location").fill(job.location);
  await page.getByLabel("Type").selectOption(job.type);
  await page.getByLabel("Min Salary").fill(String(job.salaryMin));
  await page.getByLabel("Max Salary").fill(String(job.salaryMax));
  await page.getByLabel("Description").fill(job.description);

  // Add requirements
  for (const req of job.requirements) {
    await page.getByLabel("Requirements").fill(req);
    await page.getByRole("button", { name: /add requirement/i }).click();
  }

  await page.getByRole("button", { name: /save|create|publish|post/i }).click();
}

test.describe("Job Posting and Application Flow", () => {
  test.beforeEach(async ({ page }) => {
    await loginAndNavigateToJobs(page);
  });

  test("should display jobs list page", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /jobs|positions/i }).first()
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /post|new|create|add/i })
    ).toBeVisible();
  });

  test("should create a new job posting", async ({ page }) => {
    await createJob(page);

    // Verify job appears in the list
    await expect(page.getByText(TEST_JOB.title)).toBeVisible();
    await expect(page.getByText(TEST_JOB.department)).toBeVisible();
  });

  test("should view job details", async ({ page }) => {
    await createJob(page);

    // Click on the job
    await page.getByText(TEST_JOB.title).click();

    // Verify detail view
    await expect(page.getByText(TEST_JOB.title)).toBeVisible();
    await expect(page.getByText(TEST_JOB.description)).toBeVisible();
    await expect(page.getByText(TEST_JOB.requirements[0])).toBeVisible();
  });

  test("should filter jobs by department", async ({ page }) => {
    await createJob(page);

    // Filter by department
    await page.getByLabel("Department").selectOption("Engineering");
    await expect(page.getByText(TEST_JOB.title)).toBeVisible();

    // Filter by a different department
    await page.getByLabel("Department").selectOption("Marketing");
    await expect(page.getByText(TEST_JOB.title)).not.toBeVisible();
  });

  test("should filter jobs by status", async ({ page }) => {
    await createJob(page);

    // Filter by open status
    await page.getByLabel("Status").selectOption("open");
    await expect(page.getByText(TEST_JOB.title)).toBeVisible();

    // Filter by closed status
    await page.getByLabel("Status").selectOption("closed");
    await expect(page.getByText(TEST_JOB.title)).not.toBeVisible();
  });

  test("should search jobs by title", async ({ page }) => {
    await createJob(page);

    // Search for the job
    await page.getByPlaceholder(/search/i).fill("Frontend");
    await expect(page.getByText(TEST_JOB.title)).toBeVisible();

    // Search for something that doesn't exist
    await page.getByPlaceholder(/search/i).fill("ZZZZNONEXISTENT");
    await expect(page.getByText(TEST_JOB.title)).not.toBeVisible();
  });

  test("should submit a job application", async ({ page }) => {
    await createJob(page);

    // Open job detail
    await page.getByText(TEST_JOB.title).click();

    // Click apply
    await page.getByRole("button", { name: /apply|apply now/i }).click();

    // Fill application form
    await page.getByLabel("Name").fill(TEST_APPLICATION.candidateName);
    await page.getByLabel("Email").fill(TEST_APPLICATION.candidateEmail);
    await page.getByLabel("Cover Letter").fill(TEST_APPLICATION.coverLetter);

    // Submit application
    await page.getByRole("button", { name: /submit|send|apply/i }).click();

    // Verify success
    await expect(
      page.getByText(/success|submitted|applied|thank you/i).first()
    ).toBeVisible();
  });

  test("should update job status", async ({ page }) => {
    await createJob(page);

    // Open job detail
    await page.getByText(TEST_JOB.title).click();

    // Update status
    await page.getByLabel("Status").selectOption("closed");
    await page.getByRole("button", { name: /save|update/i }).click();

    // Verify status change
    await expect(page.getByText(/closed/i)).toBeVisible();
  });

  test("should edit job posting", async ({ page }) => {
    await createJob(page);

    // Open job detail
    await page.getByText(TEST_JOB.title).click();

    // Click edit
    await page.getByRole("button", { name: /edit/i }).click();

    // Update title
    await page.getByLabel("Title").fill("Staff Frontend Engineer");
    await page.getByRole("button", { name: /save|update/i }).click();

    // Verify update
    await expect(page.getByText("Staff Frontend Engineer")).toBeVisible();
  });

  test("should delete a job posting", async ({ page }) => {
    await createJob(page);

    // Open job detail
    await page.getByText(TEST_JOB.title).click();

    // Delete
    await page.getByRole("button", { name: /delete/i }).click();

    // Confirm deletion
    await page.getByRole("button", { name: /confirm|yes|delete/i }).click();

    // Verify job is removed
    await expect(page.getByText(TEST_JOB.title)).not.toBeVisible();
  });

  test("should show job applicant count", async ({ page }) => {
    await createJob(page);

    // Open job detail
    await page.getByText(TEST_JOB.title).click();

    // Verify applicants section exists
    await expect(page.getByText(/applicants|candidates/i).first()).toBeVisible();
  });

  test("should validate required fields when creating job", async ({ page }) => {
    await page.getByRole("button", { name: /post job|new job|create job|add/i }).click();

    // Try to submit without filling required fields
    await page.getByRole("button", { name: /save|create|publish|post/i }).click();

    // Should show validation errors
    await expect(
      page.getByText(/required|invalid|error/i).first()
    ).toBeVisible();
  });
});
