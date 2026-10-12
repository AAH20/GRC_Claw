import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const script = fileURLToPath(new URL('./demo.mjs', import.meta.url));

function command(mode, outputDirectory) {
  return spawnSync(process.execPath, ['--import', 'tsx', script, mode, outputDirectory], {
    encoding: 'utf8',
  });
}

test('offline policy demo is reproducible, verifiable, and rejects ledger tampering', () => {
  const outputDirectory = mkdtempSync(join(tmpdir(), 'grc-policy-demo-'));
  try {
    const run = command('run', outputDirectory);
    assert.equal(run.status, 0, run.stderr);
    const report = JSON.parse(readFileSync(join(outputDirectory, 'report.json'), 'utf8'));
    assert.equal(report.expectedDenied, 1);
    assert.equal(report.expectedAllowed, 1);
    assert.equal(report.expectedNeedsApproval, 1);
    assert.equal(report.toolExecution, 'none; allowed action simulated');

    const verify = command('verify', outputDirectory);
    assert.equal(verify.status, 0, verify.stderr);

    const ledgerPath = join(outputDirectory, 'actions.ndjson');
    const lines = readFileSync(ledgerPath, 'utf8').trimEnd().split('\n');

    // A firewall needs_approval outcome is recorded as approval_required and never reaches a result.
    const pending = lines
      .map((line) => JSON.parse(line))
      .filter((entry) => entry.idempotencyKey === 'synthetic-approval-required-retire');
    assert.deepEqual(
      pending.map((entry) => [entry.kind, entry.executionState]),
      [['intent', 'intent_recorded'], ['decision', 'approval_required']],
    );

    const event = JSON.parse(lines[1]);
    event.decisionReason = 'tampered_decision';
    lines[1] = JSON.stringify(event);
    writeFileSync(ledgerPath, `${lines.join('\n')}\n`);
    const tampered = command('verify', outputDirectory);
    assert.equal(tampered.status, 1, 'tampered ledger should fail verification');
  } finally {
    rmSync(outputDirectory, { recursive: true, force: true });
  }
});
