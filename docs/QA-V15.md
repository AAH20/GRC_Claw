# QA Strategy — V15

## 1. Test Strategy (Layered Gates)

```
Static Gates → Domain Scripts → Build → Organic-Bootstrap → Playwright
```

| Layer | What | When | Fail Behaviour |
|-------|------|------|----------------|
| **Static Gates** | `tsc --noEmit`, ESLint, Prettier check | Every commit / PR | Block merge |
| **Domain Scripts** | `verify:auth-routes`, `verify:guest-supabase`, `test:lead-validation` | Pre-push, CI | Block push |
| **Build** | `build:dev` (Next.js production build) | Pre-push, CI | Block push |
| **Organic-Bootstrap** | `organic-bootstrap` verifies guest + PLG data seeding | Post-deploy staging | Block promote |
| **Playwright** | E2E smoke on critical guest/PLG routes | Nightly + pre-release | Block release |

---

## 2. Mandatory Pre-Push Gate

Run the full gate before **every** push:

```bash
npx tsc --noEmit \
  && npm run verify:auth-routes \
  && npm run verify:guest-supabase \
  && npm run test:lead-validation \
  && npm run build:dev \
  && npm run organic-bootstrap
```

All six commands must pass. No exceptions.

| Command | What it checks | Typical duration |
|---------|---------------|-----------------|
| `tsc --noEmit` | Type errors across all packages | 15–40 s |
| `verify:auth-routes` | Auth callback routes resolve, no missing env vars | 2–5 s |
| `verify:guest-supabase` | Guest Supabase anon key resolves, RLS policies exist | 3–8 s |
| `test:lead-validation` | Lead capture schema + edge function validation | 5–15 s |
| `build:dev` | Full Next.js build (catches import cycles, missing deps) | 60–180 s |
| `organic-bootstrap` | End-to-end seed → verify → teardown cycle | 30–60 s |

---

## 3. Change-Type Test Matrix

| What Changed | Required Tests |
|-------------|---------------|
| `api/*.ts` route | TypeCheck + `verify:auth-routes` + manual curl test |
| `api/_lib/*.ts` lib | TypeCheck + relevant domain script + `build:dev` |
| UI component (`components/`) | TypeCheck + `build:dev` + Playwright (if visible on guest/PLG) |
| Supabase migration | TypeCheck + `verify:guest-supabase` + `organic-bootstrap` |
| `middleware.ts` | TypeCheck + `verify:auth-routes` + manual browser test |
| `package.json` / deps | TypeCheck + `build:dev` + full `organic-bootstrap` |
| Cron job (`vercel.json`) | TypeCheck + `build:dev` + manual trigger test |
| Config (`next.config.js`, env) | TypeCheck + `build:dev` + full `organic-bootstrap` |
| Documentation only | None (fast-track) |

---

## 4. Functional QA Checklist

### 4.1 Guest / PLG Funnel

- [ ] `/` loads within 2 s, Lighthouse perf ≥ 85
- [ ] Guest can sign up without login (magic link or passwordless)
- [ ] Lead capture form submits, validates, stores in Supabase
- [ ] Post-signup redirect hits correct PLG dashboard
- [ ] No console errors on guest routes
- [ ] Mobile responsive (320 px–1440 px)

### 4.2 GRC Workspace

- [ ] Authenticated user sees only their org's data (RLS check)
- [ ] Framework selector loads all enabled frameworks
- [ ] Evidence upload persists to Supabase Storage
- [ ] Evidence refresh does not duplicate records
- [ ] Export quota gate blocks when quota exceeded
- [ ] Crosswalk matrix renders for all framework pairs

### 4.3 UX Honesty

- [ ] No placeholder text shipped as real content
- [ ] Loading states shown for async operations > 300 ms
- [ ] Error messages are user-friendly (no stack traces)
- [ ] Destructive actions require confirmation
- [ ] Empty states guide user to next action

---

## 5. Playwright / Responsive Testing Setup

### Installation

```bash
npm init playwright@latest -- --yes
```

### Config (`playwright.config.ts`)

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  retries: 1,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'desktop-chrome', use: { viewport: { width: 1440, height: 900 } } },
    { name: 'tablet-safari', use: { viewport: { width: 768, height: 1024 }, userAgent: 'Safari iPad' } },
    { name: 'mobile-chrome', use: { viewport: { width: 375, height: 812 } } },
  ],
});
```

### Critical Smoke Tests

| Test | Route | Assertion |
|------|-------|-----------|
| Guest home | `/` | 200, title contains product name |
| Lead capture | `/` (form) | Submit succeeds, redirect or toast |
| Auth callback | `/auth/callback` | Redirects to dashboard |
| GRC dashboard | `/grc` | Framework list renders |
| Evidence upload | `/grc/evidence` | Upload + refresh works |

### CI Integration

```yaml
# .github/workflows/playwright.yml
- run: npx playwright install --with-deps chromium
- run: npx playwright test --project=desktop-chrome
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report
    path: playwright-report/
```

---

## 6. Bug Investigation Workflow

```
1. Reproduce → capture console + network tab
2. Classify → P0 (blocker) / P1 (high) / P2 (medium) / P3 (low)
3. Bisect → git log to find introduction commit
4. Fix → minimal diff, run affected tests only
5. Verify → re-run gate, confirm regression gone
6. Document → add to CHANGELOG.md under Fixes
```

**Severity definitions:**

| Level | Definition | SLA |
|-------|-----------|-----|
| P0 | Guest funnel broken, data loss | Fix same day |
| P1 | Auth failure, RLS bypass, export broken | Fix within 24 h |
| P2 | UI glitch, slow query, missing validation | Fix within sprint |
| P3 | Cosmetic, typo, minor UX friction | Backlog |

---

## 7. Release Readiness Template

```markdown
## Release Readiness — v{X.Y.Z}

### Gate Results
- [ ] tsc --noEmit: PASS
- [ ] verify:auth-routes: PASS
- [ ] verify:guest-supabase: PASS
- [ ] test:lead-validation: PASS
- [ ] build:dev: PASS
- [ ] organic-bootstrap: PASS
- [ ] Playwright smoke: PASS (desktop + mobile)

### Functional Checklist
- [ ] Guest funnel: PASS
- [ ] GRC workspace: PASS
- [ ] UX honesty: PASS

### Performance
- [ ] Lighthouse perf ≥ 85
- [ ] API p95 < 500 ms
- [ ] Build time < 3 min

### Documentation
- [ ] CHANGELOG.md updated
- [ ] README.md reflects new features
- [ ] No broken internal links

### Sign-off
- [ ] QA: _____________
- [ ] Backend: _____________
- [ ] Product: _____________
```
