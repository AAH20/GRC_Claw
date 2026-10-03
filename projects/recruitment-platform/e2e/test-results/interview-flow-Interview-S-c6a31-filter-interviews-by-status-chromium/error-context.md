# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: interview-flow.spec.ts >> Interview Scheduling Flow >> should filter interviews by status
- Location: tests/interview-flow.spec.ts:86:7

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
  4   |  * Interview Scheduling Flow E2E Tests
  5   |  *
  6   |  * Covers interview creation, scheduling, calendar view,
  7   |  * status updates, and feedback submission.
  8   |  */
  9   | 
  10  | const TEST_INTERVIEW = {
  11  |   candidateName: "Jane Smith",
  12  |   jobTitle: "Senior Frontend Engineer",
  13  |   type: "technical" as const,
  14  |   date: "2026-10-15",
  15  |   time: "10:00",
  16  |   duration: 60,
  17  |   interviewers: ["John Manager", "Sarah Lead"],
  18  |   location: "Video Call",
  19  |   notes: "Focus on React and system design",
  20  | };
  21  | 
  22  | async function loginAndNavigateToInterviews(page: Page): Promise<void> {
  23  |   await page.goto("/login");
  24  |   await page.getByLabel("Email").fill("admin@example.com");
  25  |   await page.getByLabel("Password").fill("admin123");
  26  |   await page.getByRole("button", { name: /sign in|log in/i }).click();
> 27  |   await expect(page).toHaveURL(/\/dashboard/);
      |                      ^ Error: expect(page).toHaveURL(expected) failed
  28  |   await page.getByRole("link", { name: /interviews/i }).click();
  29  |   await expect(page).toHaveURL(/\/interviews/);
  30  | }
  31  | 
  32  | async function scheduleInterview(page: Page, interview = TEST_INTERVIEW): Promise<void> {
  33  |   await page.getByRole("button", { name: /schedule|create|new interview|add/i }).click();
  34  |   await page.getByLabel("Candidate").fill(interview.candidateName);
  35  |   await page.getByLabel("Job").fill(interview.jobTitle);
  36  |   await page.getByLabel("Type").selectOption(interview.type);
  37  |   await page.getByLabel("Date").fill(interview.date);
  38  |   await page.getByLabel("Time").fill(interview.time);
  39  |   await page.getByLabel("Duration").fill(String(interview.duration));
  40  |   await page.getByLabel("Location").fill(interview.location);
  41  |   await page.getByLabel("Notes").fill(interview.notes || "");
  42  | 
  43  |   // Add interviewers
  44  |   for (const interviewer of interview.interviewers) {
  45  |     await page.getByLabel("Interviewers").fill(interviewer);
  46  |     await page.getByRole("button", { name: /add interviewer/i }).click();
  47  |   }
  48  | 
  49  |   await page.getByRole("button", { name: /save|schedule|create|submit/i }).click();
  50  | }
  51  | 
  52  | test.describe("Interview Scheduling Flow", () => {
  53  |   test.beforeEach(async ({ page }) => {
  54  |     await loginAndNavigateToInterviews(page);
  55  |   });
  56  | 
  57  |   test("should display interviews list page", async ({ page }) => {
  58  |     await expect(
  59  |       page.getByRole("heading", { name: /interviews/i }).first()
  60  |     ).toBeVisible();
  61  |     await expect(
  62  |       page.getByRole("button", { name: /schedule|create|new|add/i })
  63  |     ).toBeVisible();
  64  |   });
  65  | 
  66  |   test("should schedule a new interview", async ({ page }) => {
  67  |     await scheduleInterview(page);
  68  | 
  69  |     // Verify interview appears in the list
  70  |     await expect(page.getByText(TEST_INTERVIEW.candidateName)).toBeVisible();
  71  |     await expect(page.getByText(TEST_INTERVIEW.jobTitle)).toBeVisible();
  72  |   });
  73  | 
  74  |   test("should view interview details", async ({ page }) => {
  75  |     await scheduleInterview(page);
  76  | 
  77  |     // Click on the interview
  78  |     await page.getByText(TEST_INTERVIEW.candidateName).click();
  79  | 
  80  |     // Verify detail view
  81  |     await expect(page.getByText(TEST_INTERVIEW.candidateName)).toBeVisible();
  82  |     await expect(page.getByText(TEST_INTERVIEW.jobTitle)).toBeVisible();
  83  |     await expect(page.getByText(TEST_INTERVIEW.location)).toBeVisible();
  84  |   });
  85  | 
  86  |   test("should filter interviews by status", async ({ page }) => {
  87  |     await scheduleInterview(page);
  88  | 
  89  |     // Filter by scheduled status
  90  |     await page.getByLabel("Status").selectOption("scheduled");
  91  |     await expect(page.getByText(TEST_INTERVIEW.candidateName)).toBeVisible();
  92  | 
  93  |     // Filter by completed status
  94  |     await page.getByLabel("Status").selectOption("completed");
  95  |     await expect(page.getByText(TEST_INTERVIEW.candidateName)).not.toBeVisible();
  96  |   });
  97  | 
  98  |   test("should filter interviews by type", async ({ page }) => {
  99  |     await scheduleInterview(page);
  100 | 
  101 |     // Filter by technical type
  102 |     await page.getByLabel("Type").selectOption("technical");
  103 |     await expect(page.getByText(TEST_INTERVIEW.candidateName)).toBeVisible();
  104 | 
  105 |     // Filter by behavioral type
  106 |     await page.getByLabel("Type").selectOption("behavioral");
  107 |     await expect(page.getByText(TEST_INTERVIEW.candidateName)).not.toBeVisible();
  108 |   });
  109 | 
  110 |   test("should update interview status to completed", async ({ page }) => {
  111 |     await scheduleInterview(page);
  112 | 
  113 |     // Open interview detail
  114 |     await page.getByText(TEST_INTERVIEW.candidateName).click();
  115 | 
  116 |     // Update status
  117 |     await page.getByLabel("Status").selectOption("completed");
  118 |     await page.getByRole("button", { name: /save|update/i }).click();
  119 | 
  120 |     // Verify status change
  121 |     await expect(page.getByText(/completed/i)).toBeVisible();
  122 |   });
  123 | 
  124 |   test("should cancel an interview", async ({ page }) => {
  125 |     await scheduleInterview(page);
  126 | 
  127 |     // Open interview detail
```