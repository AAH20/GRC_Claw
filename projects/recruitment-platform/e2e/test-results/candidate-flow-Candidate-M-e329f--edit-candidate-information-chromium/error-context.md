# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: candidate-flow.spec.ts >> Candidate Management Flow >> should edit candidate information
- Location: tests/candidate-flow.spec.ts:120:7

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
  4   |  * Candidate Management Flow E2E Tests
  5   |  *
  6   |  * Covers candidate creation, listing, filtering, detail view,
  7   |  * status updates, and deletion.
  8   |  */
  9   | 
  10  | const TEST_CANDIDATE = {
  11  |   name: "Jane Smith",
  12  |   email: "jane.smith@example.com",
  13  |   phone: "+1-555-0123",
  14  |   skills: ["React", "TypeScript", "Node.js"],
  15  |   experience: 5,
  16  |   location: "San Francisco, CA",
  17  |   notes: "Strong frontend background",
  18  | };
  19  | 
  20  | async function loginAndNavigateToCandidates(page: Page): Promise<void> {
  21  |   await page.goto("/login");
  22  |   await page.getByLabel("Email").fill("admin@example.com");
  23  |   await page.getByLabel("Password").fill("admin123");
  24  |   await page.getByRole("button", { name: /sign in|log in/i }).click();
> 25  |   await expect(page).toHaveURL(/\/dashboard/);
      |                      ^ Error: expect(page).toHaveURL(expected) failed
  26  |   await page.getByRole("link", { name: /candidates/i }).click();
  27  |   await expect(page).toHaveURL(/\/candidates/);
  28  | }
  29  | 
  30  | async function createCandidate(page: Page, candidate = TEST_CANDIDATE): Promise<void> {
  31  |   await page.getByRole("button", { name: /add candidate|new candidate|create/i }).click();
  32  |   await page.getByLabel("Name").fill(candidate.name);
  33  |   await page.getByLabel("Email").fill(candidate.email);
  34  |   await page.getByLabel("Phone").fill(candidate.phone);
  35  |   await page.getByLabel("Location").fill(candidate.location);
  36  |   await page.getByLabel("Experience").fill(String(candidate.experience));
  37  |   await page.getByLabel("Notes").fill(candidate.notes || "");
  38  | 
  39  |   // Add skills
  40  |   for (const skill of candidate.skills) {
  41  |     await page.getByLabel("Skills").fill(skill);
  42  |     await page.getByRole("button", { name: /add skill/i }).click();
  43  |   }
  44  | 
  45  |   await page.getByRole("button", { name: /save|create|submit/i }).click();
  46  | }
  47  | 
  48  | test.describe("Candidate Management Flow", () => {
  49  |   test.beforeEach(async ({ page }) => {
  50  |     await loginAndNavigateToCandidates(page);
  51  |   });
  52  | 
  53  |   test("should display candidates list page", async ({ page }) => {
  54  |     await expect(
  55  |       page.getByRole("heading", { name: /candidates/i }).first()
  56  |     ).toBeVisible();
  57  |     await expect(page.getByRole("button", { name: /add|new|create/i })).toBeVisible();
  58  |   });
  59  | 
  60  |   test("should create a new candidate", async ({ page }) => {
  61  |     await createCandidate(page);
  62  | 
  63  |     // Verify candidate appears in the list
  64  |     await expect(page.getByText(TEST_CANDIDATE.name)).toBeVisible();
  65  |     await expect(page.getByText(TEST_CANDIDATE.email)).toBeVisible();
  66  |   });
  67  | 
  68  |   test("should view candidate details", async ({ page }) => {
  69  |     await createCandidate(page);
  70  | 
  71  |     // Click on the candidate
  72  |     await page.getByText(TEST_CANDIDATE.name).click();
  73  | 
  74  |     // Verify detail view
  75  |     await expect(page.getByText(TEST_CANDIDATE.name)).toBeVisible();
  76  |     await expect(page.getByText(TEST_CANDIDATE.email)).toBeVisible();
  77  |     await expect(page.getByText(TEST_CANDIDATE.location)).toBeVisible();
  78  |     await expect(page.getByText(TEST_CANDIDATE.skills[0])).toBeVisible();
  79  |   });
  80  | 
  81  |   test("should filter candidates by status", async ({ page }) => {
  82  |     // Create a candidate first
  83  |     await createCandidate(page);
  84  | 
  85  |     // Use status filter
  86  |     await page.getByLabel("Status").selectOption("new");
  87  |     await expect(page.getByText(TEST_CANDIDATE.name)).toBeVisible();
  88  | 
  89  |     // Filter by a different status
  90  |     await page.getByLabel("Status").selectOption("hired");
  91  |     await expect(page.getByText(TEST_CANDIDATE.name)).not.toBeVisible();
  92  |   });
  93  | 
  94  |   test("should search candidates by name", async ({ page }) => {
  95  |     await createCandidate(page);
  96  | 
  97  |     // Search for the candidate
  98  |     await page.getByPlaceholder(/search/i).fill("Jane");
  99  |     await expect(page.getByText(TEST_CANDIDATE.name)).toBeVisible();
  100 | 
  101 |     // Search for something that doesn't exist
  102 |     await page.getByPlaceholder(/search/i).fill("NonExistentPerson12345");
  103 |     await expect(page.getByText(TEST_CANDIDATE.name)).not.toBeVisible();
  104 |   });
  105 | 
  106 |   test("should update candidate status", async ({ page }) => {
  107 |     await createCandidate(page);
  108 | 
  109 |     // Open candidate detail
  110 |     await page.getByText(TEST_CANDIDATE.name).click();
  111 | 
  112 |     // Update status
  113 |     await page.getByLabel("Status").selectOption("interview");
  114 |     await page.getByRole("button", { name: /save|update/i }).click();
  115 | 
  116 |     // Verify status change
  117 |     await expect(page.getByText(/interview/i)).toBeVisible();
  118 |   });
  119 | 
  120 |   test("should edit candidate information", async ({ page }) => {
  121 |     await createCandidate(page);
  122 | 
  123 |     // Open candidate detail
  124 |     await page.getByText(TEST_CANDIDATE.name).click();
  125 | 
```