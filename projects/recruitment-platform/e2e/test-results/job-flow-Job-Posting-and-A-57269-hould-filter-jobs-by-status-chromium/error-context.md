# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: job-flow.spec.ts >> Job Posting and Application Flow >> should filter jobs by status
- Location: tests/job-flow.spec.ts:104:7

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/dashboard/
Received string:  "http://localhost:3000/login"
Timeout: 5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    14 × locator resolved to <html lang="en">…</html>
       - unexpected value "http://localhost:3000/login"

```

```yaml
- link "Skip to main content":
  - /url: "#main-content"
- alert
- img
- heading "Welcome Back" [level=3]
- paragraph: Sign in to your RecruitHub account
- text: Not Found Email
- img
- textbox "Email":
  - /placeholder: you@company.com
  - text: admin@example.com
- text: Password
- img
- textbox "Password":
  - /placeholder: Enter your password
  - text: admin123
- button "Sign In"
- paragraph:
  - text: Don't have an account?
  - link "Sign up":
    - /url: /register
```

# Test source

```ts
  1   | import { test, expect, Page } from "@playwright/test";
  2   | 
  3   | /**
  4   |  * Job Posting and Application Flow E2E Tests
  5   |  *
  6   |  * Covers job creation, listing, detail view, application submission,
  7   |  * and job status management.
  8   |  */
  9   | 
  10  | const TEST_JOB = {
  11  |   title: "Senior Frontend Engineer",
  12  |   department: "Engineering",
  13  |   location: "Remote",
  14  |   type: "full-time" as const,
  15  |   salaryMin: 120000,
  16  |   salaryMax: 180000,
  17  |   description:
  18  |     "We are looking for a Senior Frontend Engineer to join our team. You will be responsible for building user interfaces using React and TypeScript.",
  19  |   requirements: ["React", "TypeScript", "Node.js", "GraphQL"],
  20  |   status: "open" as const,
  21  | };
  22  | 
  23  | const TEST_APPLICATION = {
  24  |   candidateName: "John Doe",
  25  |   candidateEmail: "john.doe@example.com",
  26  |   coverLetter: "I am very interested in this position...",
  27  | };
  28  | 
  29  | async function loginAndNavigateToJobs(page: Page): Promise<void> {
  30  |   await page.goto("/login");
  31  |   await page.getByLabel("Email").fill("admin@example.com");
  32  |   await page.getByLabel("Password").fill("admin123");
  33  |   await page.getByRole("button", { name: /sign in|log in/i }).click();
> 34  |   await expect(page).toHaveURL(/\/dashboard/);
      |                      ^ Error: expect(page).toHaveURL(expected) failed
  35  |   await page.getByRole("link", { name: /jobs|positions/i }).click();
  36  |   await expect(page).toHaveURL(/\/jobs/);
  37  | }
  38  | 
  39  | async function createJob(page: Page, job = TEST_JOB): Promise<void> {
  40  |   await page.getByRole("button", { name: /post job|new job|create job|add/i }).click();
  41  |   await page.getByLabel("Title").fill(job.title);
  42  |   await page.getByLabel("Department").fill(job.department);
  43  |   await page.getByLabel("Location").fill(job.location);
  44  |   await page.getByLabel("Type").selectOption(job.type);
  45  |   await page.getByLabel("Min Salary").fill(String(job.salaryMin));
  46  |   await page.getByLabel("Max Salary").fill(String(job.salaryMax));
  47  |   await page.getByLabel("Description").fill(job.description);
  48  | 
  49  |   // Add requirements
  50  |   for (const req of job.requirements) {
  51  |     await page.getByLabel("Requirements").fill(req);
  52  |     await page.getByRole("button", { name: /add requirement/i }).click();
  53  |   }
  54  | 
  55  |   await page.getByRole("button", { name: /save|create|publish|post/i }).click();
  56  | }
  57  | 
  58  | test.describe("Job Posting and Application Flow", () => {
  59  |   test.beforeEach(async ({ page }) => {
  60  |     await loginAndNavigateToJobs(page);
  61  |   });
  62  | 
  63  |   test("should display jobs list page", async ({ page }) => {
  64  |     await expect(
  65  |       page.getByRole("heading", { name: /jobs|positions/i }).first()
  66  |     ).toBeVisible();
  67  |     await expect(
  68  |       page.getByRole("button", { name: /post|new|create|add/i })
  69  |     ).toBeVisible();
  70  |   });
  71  | 
  72  |   test("should create a new job posting", async ({ page }) => {
  73  |     await createJob(page);
  74  | 
  75  |     // Verify job appears in the list
  76  |     await expect(page.getByText(TEST_JOB.title)).toBeVisible();
  77  |     await expect(page.getByText(TEST_JOB.department)).toBeVisible();
  78  |   });
  79  | 
  80  |   test("should view job details", async ({ page }) => {
  81  |     await createJob(page);
  82  | 
  83  |     // Click on the job
  84  |     await page.getByText(TEST_JOB.title).click();
  85  | 
  86  |     // Verify detail view
  87  |     await expect(page.getByText(TEST_JOB.title)).toBeVisible();
  88  |     await expect(page.getByText(TEST_JOB.description)).toBeVisible();
  89  |     await expect(page.getByText(TEST_JOB.requirements[0])).toBeVisible();
  90  |   });
  91  | 
  92  |   test("should filter jobs by department", async ({ page }) => {
  93  |     await createJob(page);
  94  | 
  95  |     // Filter by department
  96  |     await page.getByLabel("Department").selectOption("Engineering");
  97  |     await expect(page.getByText(TEST_JOB.title)).toBeVisible();
  98  | 
  99  |     // Filter by a different department
  100 |     await page.getByLabel("Department").selectOption("Marketing");
  101 |     await expect(page.getByText(TEST_JOB.title)).not.toBeVisible();
  102 |   });
  103 | 
  104 |   test("should filter jobs by status", async ({ page }) => {
  105 |     await createJob(page);
  106 | 
  107 |     // Filter by open status
  108 |     await page.getByLabel("Status").selectOption("open");
  109 |     await expect(page.getByText(TEST_JOB.title)).toBeVisible();
  110 | 
  111 |     // Filter by closed status
  112 |     await page.getByLabel("Status").selectOption("closed");
  113 |     await expect(page.getByText(TEST_JOB.title)).not.toBeVisible();
  114 |   });
  115 | 
  116 |   test("should search jobs by title", async ({ page }) => {
  117 |     await createJob(page);
  118 | 
  119 |     // Search for the job
  120 |     await page.getByPlaceholder(/search/i).fill("Frontend");
  121 |     await expect(page.getByText(TEST_JOB.title)).toBeVisible();
  122 | 
  123 |     // Search for something that doesn't exist
  124 |     await page.getByPlaceholder(/search/i).fill("ZZZZNONEXISTENT");
  125 |     await expect(page.getByText(TEST_JOB.title)).not.toBeVisible();
  126 |   });
  127 | 
  128 |   test("should submit a job application", async ({ page }) => {
  129 |     await createJob(page);
  130 | 
  131 |     // Open job detail
  132 |     await page.getByText(TEST_JOB.title).click();
  133 | 
  134 |     // Click apply
```