import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const script = fileURLToPath(new URL('./demo.mjs', import.meta.url));
const STATUSES = ['pass', 'fail', 'unknown', 'not_applicable'];
const PROVENANCE = ['repository_reported', 'fixture_backed', 'independently_verified'];

function demo(mode, dir) {
  return spawnSync(process.execPath, ['--import', 'tsx', script, mode, dir], {
    encoding: 'utf8',
    env: { ...process.env, NO_COLOR: '1' },
  });
}

function freshRun(t) {
  const dir = mkdtempSync(join(tmpdir(), 'grc-claw-evidence-chain-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const result = demo('run', dir);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return { dir, report: JSON.parse(readFileSync(join(dir, 'report.json'), 'utf8')) };
}

test('every stage matches the fixture and only the allowed action reaches a tool', (t) => {
  const { report } = freshRun(t);

  assert.deepEqual(
    report.cases.map((c) => [c.tool, c.outcome, c.boundaryState, c.toolInvoked]),
    [
      ['inventory.read', 'allowed', 'execute', true],
      ['control.update', 'needs_approval', 'interrupt', false],
      ['customer.export', 'denied', 'deny', false],
    ],
  );
  assert.deepEqual(report.verification.cases.map((c) => c.ledgerStates), [
    ['intent_recorded', 'executing', 'simulated'],
    ['intent_recorded', 'approval_required'],
    ['intent_recorded', 'denied'],
  ]);
  assert.equal(report.cases[1].approvalRequest.receiptHash, report.cases[1].receiptHash);

  assert.deepEqual(report.summary, { total: 23, pass: 22, fail: 0, unknown: 0, not_applicable: 1 });
  for (const check of report.checks) {
    assert.ok(STATUSES.includes(check.status), `${check.id}: status ${check.status}`);
    assert.ok(PROVENANCE.includes(check.provenance), `${check.id}: provenance ${check.provenance}`);
  }
  assert.equal(report.checks.find((check) => check.id === 'approval.resume').status, 'not_applicable');

  assert.match(report.fixture.sha256, /^[0-9a-f]{64}$/);
  assert.equal(report.fixture.file, 'examples/approval-evidence-chain/fixture.v1.json');
  assert.ok(report.commit.sha);
  assert.equal(report.environment.node, process.version);
  assert.ok(report.limitations.length > 0);
});

test('verify recomputes the recorded artifacts', (t) => {
  const { dir } = freshRun(t);
  const result = demo('verify', dir);
  assert.equal(result.status, 0, result.stdout);
  assert.match(result.stdout, /Result {2}verified/);
});

test('the deterministic digest is identical across runs while receipt IDs differ', (t) => {
  const first = freshRun(t).report;
  const second = freshRun(t).report;
  assert.equal(first.deterministicDigest, second.deterministicDigest);
  assert.notEqual(first.cases[0].receiptId, second.cases[0].receiptId);
});

test('verify rejects tampered artifacts', async (t) => {
  const mutations = {
    'a receipt outcome changed to allowed': (dir) => {
      const receipts = JSON.parse(readFileSync(join(dir, 'receipts.json'), 'utf8'));
      receipts[1].decision.outcome = 'allowed';
      receipts[1].decision.allowed = true;
      writeFileSync(join(dir, 'receipts.json'), JSON.stringify(receipts));
      return 'update-control.receipt';
    },
    'evidence-node controlIds changed': (dir) => {
      const nodes = JSON.parse(readFileSync(join(dir, 'evidence-nodes.json'), 'utf8'));
      nodes[0].controlIds = ['TAMPERED-CONTROL'];
      writeFileSync(join(dir, 'evidence-nodes.json'), JSON.stringify(nodes));
      return 'read-inventory.evidence';
    },
    'a ledger event edited': (dir) => {
      const lines = readFileSync(join(dir, 'ledger.ndjson'), 'utf8').trimEnd().split('\n');
      const event = JSON.parse(lines[1]);
      event.decisionReason = 'tampered_decision';
      lines[1] = JSON.stringify(event);
      writeFileSync(join(dir, 'ledger.ndjson'), `${lines.join('\n')}\n`);
      return 'ledger.chain';
    },
    'a report status rewritten': (dir) => {
      const report = JSON.parse(readFileSync(join(dir, 'report.json'), 'utf8'));
      report.checks.find((check) => check.id === 'export-customers.execution').status = 'fail';
      writeFileSync(join(dir, 'report.json'), JSON.stringify(report));
      return 'report digest';
    },
  };

  for (const [name, mutate] of Object.entries(mutations)) {
    await t.test(name, (st) => {
      const { dir } = freshRun(st);
      const expectedProblem = mutate(dir);
      const result = demo('verify', dir);
      assert.equal(result.status, 1, `${name} was not detected:\n${result.stdout}`);
      assert.ok(result.stdout.includes(expectedProblem), `expected "${expectedProblem}" in:\n${result.stdout}`);
    });
  }
});
