import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { AgentPolicyFirewall } from '../../packages/agent-policy-firewall/src/index.ts';
import { ActionLedger } from '../../packages/evidence/src/action-ledger.ts';

const here = dirname(fileURLToPath(import.meta.url));
const fixture = JSON.parse(readFileSync(join(here, 'fixture.json'), 'utf8'));
const defaultOutput = join(here, 'out');

// The ledger keeps approval_required as its canonical state for a firewall needs_approval outcome.
const ledgerStateForOutcome = { allowed: 'executing', denied: 'denied', needs_approval: 'approval_required' };

function usage() {
  console.error('Usage: node --import tsx examples/agent-policy-denial/demo.mjs <run|verify> [output-directory]');
  process.exitCode = 2;
}

function evaluateCase(firewall, scenario) {
  return firewall.evaluate(
    fixture.actor,
    { toolName: scenario.toolName, tier: scenario.tier, args: scenario.args },
    fixture.context,
  );
}

function verify(outputDirectory) {
  const ledgerPath = join(outputDirectory, 'actions.ndjson');
  assert.ok(existsSync(ledgerPath), 'missing actions.ndjson');
  const ledger = new ActionLedger(ledgerPath);
  const integrity = ledger.verify();
  assert.equal(integrity.ok, true, `ledger integrity: ${integrity.error ?? 'unknown error'}`);

  const events = ledger.list(500).reverse();
  const firewall = new AgentPolicyFirewall();
  let offset = 0;
  let allowed = 0;
  let denied = 0;
  let needsApproval = 0;

  for (const scenario of fixture.cases) {
    const expected = evaluateCase(firewall, scenario);
    assert.equal(expected.allowed, scenario.expectedAllowed, `fixture mismatch: ${scenario.id}`);
    assert.equal(expected.outcome, scenario.expectedOutcome, `fixture outcome mismatch: ${scenario.id}`);
    assert.equal(expected.reason, scenario.expectedReason, `fixture reason mismatch: ${scenario.id}`);

    const intent = events[offset++];
    const decision = events[offset++];
    assert.equal(intent?.kind, 'intent', `missing intent: ${scenario.id}`);
    assert.equal(intent?.tool, scenario.toolName, `tool mismatch: ${scenario.id}`);
    assert.equal(intent?.tenantId, fixture.actor.tenantId, `tenant mismatch: ${scenario.id}`);
    assert.equal(intent?.sessionId, 'synthetic-policy-demo', `session mismatch: ${scenario.id}`);
    assert.equal(intent?.idempotencyKey, `synthetic-${scenario.id}`, `case linkage mismatch: ${scenario.id}`);
    assert.equal(intent?.argsHash, createHash('sha256').update(JSON.stringify(scenario.args)).digest('hex'), `arguments differ from fixture: ${scenario.id}`);
    assert.deepEqual(intent?.argKeys, Object.keys(scenario.args).sort(), `argument keys differ from fixture: ${scenario.id}`);
    assert.equal(decision?.kind, 'decision', `missing decision: ${scenario.id}`);
    assert.equal(decision?.actionId, intent.actionId, `action linkage mismatch: ${scenario.id}`);
    assert.equal(decision?.decisionReason, expected.reason, `reason mismatch: ${scenario.id}`);
    assert.equal(decision?.executionState, ledgerStateForOutcome[expected.outcome], `decision mismatch: ${scenario.id}`);
    assert.equal(decision?.requiresApproval, expected.requiresApproval, `approval flag mismatch: ${scenario.id}`);

    if (expected.outcome === 'allowed') {
      const result = events[offset++];
      assert.equal(result?.kind, 'result', `missing simulated result: ${scenario.id}`);
      assert.equal(result?.actionId, intent.actionId, `result linkage mismatch: ${scenario.id}`);
      assert.equal(result?.executionState, 'simulated', `unexpected execution: ${scenario.id}`);
      allowed++;
    } else if (expected.outcome === 'needs_approval') {
      needsApproval++;
    } else {
      denied++;
    }
  }

  assert.equal(offset, events.length, 'unexpected extra ledger events');
  const rawLedger = readFileSync(ledgerPath, 'utf8');
  for (const scenario of fixture.cases) {
    for (const value of Object.values(scenario.args)) {
      if (typeof value === 'string') assert.equal(rawLedger.includes(value), false, `raw argument leaked: ${scenario.id}`);
    }
  }

  const result = {
    classification: fixture.classification,
    fixtureCases: fixture.cases.length,
    expectedAllowed: allowed,
    expectedDenied: denied,
    expectedNeedsApproval: needsApproval,
    observedLedgerEvents: events.length,
    ledgerIntegrity: 'verified',
    rawArgumentDisclosure: 'none-observed',
    toolExecution: 'none; allowed action simulated',
  };
  if (existsSync(join(outputDirectory, 'report.json'))) {
    const report = JSON.parse(readFileSync(join(outputDirectory, 'report.json'), 'utf8'));
    assert.deepEqual(report, result, 'report differs from verified ledger');
  }
  return result;
}

function run(outputDirectory) {
  mkdirSync(outputDirectory, { recursive: true });
  const ledgerPath = join(outputDirectory, 'actions.ndjson');
  assert.equal(existsSync(ledgerPath), false, 'output already contains a ledger; use a fresh directory');
  const ledger = new ActionLedger(ledgerPath);
  const firewall = new AgentPolicyFirewall();

  for (const scenario of fixture.cases) {
    const request = { toolName: scenario.toolName, tier: scenario.tier, args: scenario.args };
    const intent = ledger.recordIntent({
      tenantId: fixture.actor.tenantId,
      sessionId: 'synthetic-policy-demo',
      tool: scenario.toolName,
      args: scenario.args,
      idempotencyKey: `synthetic-${scenario.id}`,
    });
    const decision = firewall.evaluate(fixture.actor, request, fixture.context);
    assert.equal(decision.allowed, scenario.expectedAllowed, `unexpected policy outcome: ${scenario.id}`);
    assert.equal(decision.outcome, scenario.expectedOutcome, `unexpected firewall outcome: ${scenario.id}`);
    assert.equal(decision.reason, scenario.expectedReason, `unexpected policy reason: ${scenario.id}`);
    ledger.recordDecision(intent, {
      allowed: decision.allowed,
      reason: decision.reason,
      requiresApproval: decision.requiresApproval,
      outcome: decision.outcome,
    });
    // This demo never invokes any tool. Only the permitted path records a simulated result;
    // an action awaiting approval stops at its decision.
    if (decision.outcome === 'allowed') ledger.recordResult(intent, { executionState: 'simulated' });
  }

  const result = verify(outputDirectory);
  writeFileSync(join(outputDirectory, 'report.json'), `${JSON.stringify(result, null, 2)}\n`);
  return result;
}

const [command, outputArg] = process.argv.slice(2);
if (command !== 'run' && command !== 'verify') usage();
else {
  try {
    const outputDirectory = resolve(outputArg ?? defaultOutput);
    const result = command === 'run' ? run(outputDirectory) : verify(outputDirectory);
    console.log(JSON.stringify({ outputDirectory, ...result }, null, 2));
  } catch (error) {
    console.error(`agent policy denial ${command} failed: ${error.message}`);
    process.exitCode = 1;
  }
}
