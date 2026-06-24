/** GRC_Claw action-ledger contract test. */
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ActionLedger } from '../packages/evidence/dist/index.js';

const dir = mkdtempSync(join(tmpdir(), 'grc-claw-ledger-'));
const path = join(dir, 'actions.ndjson');

try {
  const ledger = new ActionLedger(path);
  const intent = ledger.recordIntent({
    tenantId: 7,
    sessionId: 'test-session',
    tool: 'evidence.attach',
    args: { controlId: 'AC.1', content: 'never-write-raw-evidence-to-ledger' },
    idempotencyKey: 'action-ledger-test-1',
  });
  ledger.recordDecision(intent, { allowed: true, reason: 'write_allowed', requiresApproval: false });
  ledger.recordResult(intent, { executionState: 'recorded', evidenceId: 'ev-test' });

  const persisted = new ActionLedger(path);
  assert.equal(persisted.verify().ok, true);
  assert.equal(persisted.list().length, 3);
  assert.equal(persisted.list()[0]?.executionState, 'recorded');
  assert.equal(readFileSync(path, 'utf8').includes('never-write-raw-evidence-to-ledger'), false);
  console.log('action ledger: 4 passed, 0 failed');
} finally {
  rmSync(dir, { recursive: true, force: true });
}
