# Backend Engineering Standards — V15

## 1. Thin Routes Principle

Every `api/*.ts` file is a **thin route** — it parses input, delegates to `api/_lib/`, and returns the result.

```ts
// api/evidence/upload.ts — GOOD
import { NextRequest, NextResponse } from 'next/server';
import { handleEvidenceUpload } from '../_lib/evidence/upload';

export async function POST(req: NextRequest) {
  const result = await handleEvidenceUpload(req);
  return NextResponse.json(result);
}

// api/evidence/upload.ts — BAD (logic in route)
export async function POST(req: NextRequest) {
  const form = await req.formData();
  const file = form.get('file');
  // 100 lines of processing...
}
```

**Rules:**
- Route files: max 20 lines (parse + delegate + respond)
- All business logic lives in `api/_lib/`
- Route files never import database clients directly
- Route files never call Supabase client directly — go through `_lib/`

---

## 2. Org Scope

**Every database query includes `organization_id`.**

```ts
// GOOD — org-scoped
const { data } = await supabase
  .from('evidence_items')
  .select('*')
  .eq('organization_id', orgId);

// BAD — missing org scope (reads all tenants' data)
const { data } = await supabase
  .from('evidence_items')
  .select('*');
```

**Pattern:**

```ts
// api/_lib/org-scope.ts
export function withOrgScope(query: any, orgId: string) {
  return query.eq('organization_id', orgId);
}
```

**RLS is a safety net, not a replacement** for explicit org scoping. Always include `organization_id` in queries even when RLS is enabled.

---

## 3. Idempotency

All mutating operations must be idempotent.

### Stable Keys

```ts
const idempotencyKey = `evidence:${orgId}:${frameworkId}:${contentHash}`;
```

### Content Hash

```ts
import { createHash } from 'crypto';

function contentHash(buffer: Buffer): string {
  return createHash('sha256').update(buffer).digest('hex').slice(0, 16);
}
```

### Daily Dedupe

For cron jobs and batch operations:

```ts
const today = new Date().toISOString().slice(0, 10);
const dedupKey = `refresh:${orgId}:${today}`;

const existing = await supabase
  .from('job_runs')
  .select('id')
  .eq('dedup_key', dedupKey)
  .single();

if (existing.data) {
  return { skipped: true, reason: 'already_run_today' };
}
```

---

## 4. Bounded Work

Vercel functions have a **10 s (Hobby) or 60 s (Pro)** timeout. All cron jobs must be capped.

```ts
const MAX_ITEMS_PER_RUN = 50;
const MAX_PROCESSING_MS = 8_000; // leave 2 s buffer

async function processBatch(items: Item[]) {
  const start = Date.now();
  let processed = 0;

  for (const item of items.slice(0, MAX_ITEMS_PER_RUN)) {
    if (Date.now() - start > MAX_PROCESSING_MS) {
      console.log(`[bounded] Timeout approaching, stopping at ${processed}/${items.length}`);
      break;
    }
    await processItem(item);
    processed++;
  }

  return { processed, total: items.length, bounded: true };
}
```

**Rules:**
- Max 50 items per cron invocation
- Hard 8 s processing budget (60 s endpoint)
- Log when bounded — never silently drop
- Use `void fn().catch()` for fire-and-forget

---

## 5. Gate Before Side Effects

Every export, mutation, or external call follows:

```
checkGrcAction → consumeExportQuota → mutate → respond
```

```ts
export async function handleExport(req: NextRequest) {
  const { orgId, action } = await parseRequest(req);

  // 1. Gate: check if action is allowed
  const gate = await checkGrcAction(orgId, action);
  if (!gate.allowed) {
    return NextResponse.json({ error: gate.reason }, { status: 403 });
  }

  // 2. Gate: consume quota
  const quota = await consumeExportQuota(orgId, action);
  if (!quota.success) {
    return NextResponse.json({ error: 'quota_exceeded' }, { status: 429 });
  }

  // 3. Mutate (only after gates pass)
  const result = await performExport(orgId, action);

  // 4. Respond
  return NextResponse.json(result);
}
```

**Never skip gates.** Even if the caller "should" have access, always check.

---

## 6. Async Refresh

Post-ingest evidence refresh runs asynchronously via fire-and-forget:

```ts
// GOOD — async, non-blocking
void refreshEvidenceEvidence(evidenceId).catch((err) => {
  console.error(`[async-refresh] Failed for ${evidenceId}:`, err);
});

// BAD — blocks the response
await refreshEvidenceEvidence(evidenceId);
return NextResponse.json({ done: true });
```

**Rules:**
- Use `void fn().catch()` pattern
- Always catch and log errors
- Never await fire-and-forget operations in request handlers
- Async refreshes should complete within 30 s

---

## 7. Security Checklist

| Check | Enforced By |
|-------|------------|
| No cross-tenant reads | `organization_id` in every query + RLS |
| `clampJson` on all JSONB inputs | `api/_lib/validate.ts` |
| Export quota gates | `api/_lib/gate.ts` |
| Bridge auth on webhook endpoints | `api/_lib/bridge-auth.ts` |
| No secrets in logs | ESLint rule + manual review |
| Rate limiting on public endpoints | Vercel edge middleware |
| CORS restricted to known origins | `next.config.js` headers |
| No `eval()` or dynamic imports from user input | ESLint `no-eval` |

### clampJson

```ts
export function clampJson(input: unknown, maxDepth = 5, maxSize = 10_000): string {
  const safe = sanitizeDepth(input, maxDepth);
  const str = JSON.stringify(safe);
  if (str.length > maxSize) {
    throw new Error(`JSON too large: ${str.length} > ${maxSize}`);
  }
  return str;
}
```

### Bridge Auth

```ts
export async function verifyBridgeAuth(req: NextRequest): Promise<string | null> {
  const token = req.headers.get('x-bridge-token');
  if (!token) return null;
  const valid = await verifyToken(token);
  return valid ? valid.orgId : null;
}
```

---

## 8. PLG + Backend Integration Patterns

### Lead Capture → Org Provisioning

```ts
// api/_lib/plg/lead-capture.ts
export async function captureLead(input: LeadInput) {
  // 1. Validate schema
  const validated = LeadSchema.parse(input);

  // 2. Check idempotency
  const existing = await findLeadByEmail(validated.email);
  if (existing) return { id: existing.id, duplicate: true };

  // 3. Create lead record
  const lead = await insertLead(validated);

  // 4. Async: provision org (fire-and-forget)
  void provisionOrgForLead(lead.id).catch(console.error);

  return { id: lead.id, duplicate: false };
}
```

### PLG Dashboard → GRC Data

```ts
// api/_lib/plg/dashboard.ts
export async function getPlgDashboard(orgId: string) {
  const [controls, evidence, frameworks] = await Promise.all([
    getControlSummary(orgId),
    getEvidenceStats(orgId),
    getEnabledFrameworks(orgId),
  ]);

  return { controls, evidence, frameworks };
}
```

### PLG Limits → Export Gates

```ts
// api/_lib/plg/limits.ts
export function checkPlgLimits(orgId: string, tier: string) {
  const limits = PLG_TIER_LIMITS[tier];
  return {
    maxFrameworks: limits.frameworks,
    maxEvidence: limits.evidence,
    maxExports: limits.exports,
  };
}
```

**PLG tier limits are enforced at the gate layer, not in route handlers.**

---

## Appendix: File Naming Conventions

| Location | Convention | Example |
|----------|-----------|---------|
| `api/*.ts` | kebab-case route | `api/evidence/upload.ts` |
| `api/_lib/*.ts` | camelCase module | `api/_lib/evidence/upload.ts` |
| `api/_lib/validate.ts` | Shared validators | `clampJson`, `parseBody` |
| `api/_lib/gate.ts` | Shared gates | `checkGrcAction`, `consumeExportQuota` |
| `api/_lib/bridge-auth.ts` | Bridge webhook auth | `verifyBridgeAuth` |
