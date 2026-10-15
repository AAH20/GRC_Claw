// Approval boundary and evidence chain: an offline, reproducible demonstration.
//
//   run    [dir]  Sends each fixture case through policy evaluation, the DeepAgents adapter boundary, the
//                 execution decision, the action ledger, the firewall receipt and the evidence graph, writes the
//                 artifacts, verifies them from disk, runs tamper checks and writes report.json.
//   verify [dir]  Re-reads the artifacts, recomputes every verification and checks the report against them.
//                 Exits 1 on any mismatch.
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { arch, cpus, platform, tmpdir } from 'node:os';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  AgentPolicyFirewall,
  formatFirewallReceiptForEvidenceGraph,
  verifyFirewallReceipt,
} from '../../packages/agent-policy-firewall/src/index.ts';
import { assertExecutable, toDeepAgentsApprovalResult } from '../../packages/deepagents-approval-adapter/src/index.ts';
import { ActionLedger } from '../../packages/evidence/src/action-ledger.ts';
import { evidenceObjectHash, nodeObject } from '../../packages/evidence-graph/src/index.ts';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, '..', '..');
const fixtureFile = join(here, 'fixture.v1.json');
// Hash the fixture with LF line endings so the digest is identical on every platform and checkout.
const fixtureText = readFileSync(fixtureFile, 'utf8').replace(/\r\n/g, '\n');
const fixture = JSON.parse(fixtureText);
const ARTIFACTS = { ledger: 'ledger.ndjson', receipts: 'receipts.json', nodes: 'evidence-nodes.json', report: 'report.json' };
const LIMITATIONS = [
  'Synthetic, offline fixture: no real tool, model or external service is called, and tool results are simulated.',
  'Reference demonstration, not a production integration.',
  "Verification recomputes the artifacts with this repository's own verifiers (verifyFirewallReceipt, ActionLedger.verify, evidenceObjectHash). It is not a third-party audit.",
  'Receipt IDs, action IDs and timestamps differ per run. The deterministic digest covers only the fields that must not change.',
];

const sha256 = (text) => createHash('sha256').update(text).digest('hex');
const stable = (value) => {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  }
  return value;
};
const readJson = (dir, name) => JSON.parse(readFileSync(join(dir, name), 'utf8'));
const writeJson = (dir, name, value) => writeFileSync(join(dir, name), `${JSON.stringify(value, null, 2)}\n`);
const caseKey = (scenario) => `${fixture.id}-${scenario.id}`;
const sameList = (a, b) => JSON.stringify(a) === JSON.stringify(b);

const color = process.stdout.isTTY && !process.env.NO_COLOR;
const paint = (code) => (text) => (color ? `\u001b[${code}m${text}\u001b[0m` : text);
const bold = paint('1');
const dim = paint('2');
const green = paint('32');
const red = paint('31');
const yellow = paint('33');
const STATUS_LABEL = { pass: green('PASS'), fail: red('FAIL'), unknown: yellow('UNKNOWN'), not_applicable: yellow('N/A ') };

function commitInfo() {
  const git = (args) => spawnSync('git', args, { cwd: repoRoot, encoding: 'utf8' });
  const head = git(['rev-parse', 'HEAD']);
  if (head.status !== 0) return { sha: 'unknown', worktreeClean: null };
  const status = git(['status', '--porcelain', '--untracked-files=no']);
  return { sha: head.stdout.trim(), worktreeClean: status.status === 0 ? status.stdout.trim() === '' : null };
}

function environment() {
  return { node: process.version, platform: platform(), arch: arch(), cpu: cpus()[0]?.model?.trim() ?? 'unknown' };
}

/** Synthetic tools. They record each invocation so the boundary's effect is observable. */
function syntheticTools() {
  const invocations = [];
  const tools = {
    'inventory.read': (args) => ({ assetId: args.assetId, status: 'in_service' }),
    'control.update': (args) => ({ controlId: args.controlId, updated: true }),
    'customer.export': (args) => ({ dataset: args.dataset, rows: 0 }),
  };
  return {
    invocations,
    invoke(name, args) {
      invocations.push(name);
      return tools[name](args);
    },
  };
}

/** Independent verification: reads only the written artifacts and recomputes every check. */
function verifyArtifacts(dir) {
  const receipts = readJson(dir, ARTIFACTS.receipts);
  const nodes = readJson(dir, ARTIFACTS.nodes);
  const ledger = new ActionLedger(join(dir, ARTIFACTS.ledger));
  const chain = ledger.verify();
  const events = ledger.list(500).reverse();
  const cases = fixture.cases.map((scenario, index) => {
    const receipt = receipts[index];
    const node = nodes[index];
    return {
      id: scenario.id,
      receiptVerified: Boolean(receipt) && verifyFirewallReceipt(receipt),
      nodeHashRecomputed: Boolean(node) && evidenceObjectHash(node) === node.objectHash,
      nodeBoundToReceipt: Boolean(node && receipt)
        && node.payload?.receipt_hash === receipt.receiptHash
        && node.payload?.receipt_id === receipt.receiptId,
      ledgerStates: events.filter((event) => event.idempotencyKey === caseKey(scenario)).map((event) => event.executionState),
    };
  });
  return { chain: { ok: chain.ok, checked: chain.checked }, cases };
}

/** Checks whose evidence is the written artifacts; `verify` recomputes exactly these. */
function artifactChecks(verification) {
  const checks = [];
  verification.cases.forEach((observed, index) => {
    const scenario = fixture.cases[index];
    checks.push({
      id: `${scenario.id}.ledger`,
      title: 'Ledger records the expected state sequence',
      status: sameList(observed.ledgerStates, scenario.expected.ledgerStates) ? 'pass' : 'fail',
      provenance: 'fixture_backed',
      observed: { artifact: ARTIFACTS.ledger, states: observed.ledgerStates },
    });
    checks.push({
      id: `${scenario.id}.receipt`,
      title: 'Receipt verifies against its bound decision fields',
      status: observed.receiptVerified ? 'pass' : 'fail',
      provenance: 'independently_verified',
      observed: { artifact: ARTIFACTS.receipts, index },
    });
    checks.push({
      id: `${scenario.id}.evidence`,
      title: 'Evidence-node hash recomputes from the complete node and is bound to the receipt',
      status: observed.nodeHashRecomputed && observed.nodeBoundToReceipt ? 'pass' : 'fail',
      provenance: 'independently_verified',
      observed: { artifact: ARTIFACTS.nodes, index },
    });
  });
  checks.push({
    id: 'ledger.chain',
    title: 'Ledger hash chain verifies',
    status: verification.chain.ok ? 'pass' : 'fail',
    provenance: 'independently_verified',
    observed: { artifact: ARTIFACTS.ledger, events: verification.chain.checked },
  });
  return checks;
}

/** Deliberate mutations of the observed artifacts. Each one must be detected. */
function tamperChecks(dir, receipts, nodes) {
  // Locate the pending case through the fixture, not the receipt, so a tampered receipt cannot hide it.
  const pending = receipts[fixture.cases.findIndex((scenario) => scenario.expected.outcome === 'needs_approval')];
  const flipped = { ...pending, decision: { ...pending.decision, outcome: 'allowed', allowed: true } };

  const controlsChanged = { ...nodes[0], controlIds: ['TAMPERED-CONTROL'] };

  const lines = readFileSync(join(dir, ARTIFACTS.ledger), 'utf8').trimEnd().split('\n');
  const edited = JSON.parse(lines[1]);
  edited.decisionReason = 'tampered_decision';
  lines[1] = JSON.stringify(edited);
  const scratch = mkdtempSync(join(tmpdir(), 'grc-claw-tamper-'));
  let ledgerDetected;
  try {
    writeFileSync(join(scratch, ARTIFACTS.ledger), `${lines.join('\n')}\n`);
    ledgerDetected = !new ActionLedger(join(scratch, ARTIFACTS.ledger)).verify().ok;
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }

  return [
    {
      id: 'tamper.receipt-outcome',
      title: 'Changing needs_approval to allowed in a receipt fails verification',
      status: verifyFirewallReceipt(pending) && !verifyFirewallReceipt(flipped) ? 'pass' : 'fail',
      provenance: 'fixture_backed',
      observed: { artifact: ARTIFACTS.receipts, mutation: 'decision.outcome needs_approval -> allowed' },
    },
    {
      id: 'tamper.evidence-controls',
      title: 'Changing controlIds on an evidence node changes its hash',
      status: evidenceObjectHash(controlsChanged) !== nodes[0].objectHash ? 'pass' : 'fail',
      provenance: 'fixture_backed',
      observed: { artifact: ARTIFACTS.nodes, mutation: 'controlIds -> [TAMPERED-CONTROL]' },
    },
    {
      id: 'tamper.ledger-event',
      title: 'Editing a ledger event breaks the hash chain',
      status: ledgerDetected ? 'pass' : 'fail',
      provenance: 'fixture_backed',
      observed: { artifact: ARTIFACTS.ledger, mutation: 'event 2 decisionReason edited' },
    },
  ];
}

function digestOf(fixtureSha, cases, checks) {
  return sha256(JSON.stringify(stable({
    fixtureSha,
    cases: cases.map((c) => ({ id: c.id, outcome: c.outcome, reason: c.reason, boundaryState: c.boundaryState, toolInvoked: c.toolInvoked })),
    checks: checks.map((c) => [c.id, c.status, c.provenance]),
  })));
}

function summarize(checks) {
  const summary = { total: checks.length, pass: 0, fail: 0, unknown: 0, not_applicable: 0 };
  for (const check of checks) summary[check.status] += 1;
  return summary;
}

function run(dir) {
  mkdirSync(dir, { recursive: true });
  for (const name of Object.values(ARTIFACTS)) {
    if (existsSync(join(dir, name))) throw new Error(`${relative(repoRoot, join(dir, name))} already exists; use a fresh output directory`);
  }

  const ledger = new ActionLedger(join(dir, ARTIFACTS.ledger));
  const firewall = new AgentPolicyFirewall();
  const tools = syntheticTools();
  const receipts = [];
  const nodes = [];
  const cases = [];
  const stageChecks = [];

  for (const scenario of fixture.cases) {
    const { request, expected } = scenario;
    const intent = ledger.recordIntent({
      tenantId: fixture.actor.tenantId,
      sessionId: fixture.sessionId,
      tool: request.toolName,
      args: request.args,
      idempotencyKey: caseKey(scenario),
    });

    // Policy evaluation and the adapter boundary (decision + receipt).
    const boundary = toDeepAgentsApprovalResult(firewall, { actor: fixture.actor, request, context: fixture.context });
    const { decision, receipt } = boundary;
    ledger.recordDecision(intent, {
      allowed: decision.allowed,
      reason: decision.reason,
      requiresApproval: decision.requiresApproval,
      outcome: decision.outcome,
    });

    // Execution decision: the host invokes a tool only for an `execute` result.
    const invocationsBefore = tools.invocations.length;
    if (boundary.state === 'execute') {
      assertExecutable(boundary);
      const output = tools.invoke(request.toolName, request.args);
      ledger.recordResult(intent, { executionState: 'simulated', output });
    }
    const toolInvoked = tools.invocations.length > invocationsBefore;

    // Evidence-graph projection: the formatter binds the payload to the receipt; nodeObject() hashes the node.
    const formatted = formatFirewallReceiptForEvidenceGraph(receipt);
    const node = nodeObject({
      orgSlug: fixture.orgSlug,
      graphId: `fw_receipt:${receipt.receiptId}`,
      objectType: 'policy_decision',
      label: String(formatted.label),
      source: 'agent-policy-firewall',
      controlIds: decision.controlImpact,
      payload: formatted.payload,
    });
    receipts.push(receipt);
    nodes.push(node);

    const observed = {
      id: scenario.id,
      tool: request.toolName,
      tier: request.tier,
      outcome: decision.outcome,
      reason: decision.reason,
      boundaryState: boundary.state,
      toolInvoked,
      approvalRequest: decision.outcome === 'needs_approval'
        ? { receiptHash: receipt.receiptHash, approvalThreshold: decision.approvalThreshold, reason: decision.reason }
        : null,
      receiptId: receipt.receiptId,
      receiptHash: receipt.receiptHash,
      nodeObjectHash: node.objectHash,
    };
    cases.push(observed);

    stageChecks.push(
      {
        id: `${scenario.id}.policy`,
        title: 'Policy outcome and reason match the fixture',
        status: observed.outcome === expected.outcome && observed.reason === expected.reason ? 'pass' : 'fail',
        provenance: 'fixture_backed',
        observed: { outcome: observed.outcome, reason: observed.reason },
      },
      {
        id: `${scenario.id}.boundary`,
        title: 'Adapter boundary state matches the fixture',
        status: observed.boundaryState === expected.boundaryState ? 'pass' : 'fail',
        provenance: 'fixture_backed',
        observed: { boundaryState: observed.boundaryState },
      },
      {
        id: `${scenario.id}.execution`,
        title: expected.toolInvoked ? 'Tool is invoked' : 'Tool is never invoked',
        status: observed.toolInvoked === expected.toolInvoked ? 'pass' : 'fail',
        provenance: 'fixture_backed',
        observed: { toolInvoked: observed.toolInvoked },
      },
    );
  }

  writeJson(dir, ARTIFACTS.receipts, receipts);
  writeJson(dir, ARTIFACTS.nodes, nodes);

  // Verification uses only what was written to disk.
  const verification = verifyArtifacts(dir);
  const checks = [
    ...stageChecks,
    ...artifactChecks(verification),
    ...tamperChecks(dir, readJson(dir, ARTIFACTS.receipts), readJson(dir, ARTIFACTS.nodes)),
    {
      id: 'approval.resume',
      title: 'An approved action resumes through the boundary',
      status: 'not_applicable',
      provenance: 'repository_reported',
      observed: null,
      limitation: 'The resume path after human approval is not implemented in this repository yet.',
    },
  ];
  const fixtureSha = sha256(fixtureText);
  const report = {
    schema: 'grc-claw.demo-report/v1',
    demo: fixture.id,
    generatedAt: new Date().toISOString(),
    commit: commitInfo(),
    environment: environment(),
    fixture: {
      id: fixture.id,
      version: fixture.version,
      file: toPosix(relative(repoRoot, fixtureFile)),
      sha256: fixtureSha,
      classification: fixture.classification,
    },
    artifacts: Object.values(ARTIFACTS),
    cases,
    verification,
    checks,
    summary: summarize(checks),
    deterministicDigest: digestOf(fixtureSha, cases, checks),
    limitations: LIMITATIONS,
  };
  writeJson(dir, ARTIFACTS.report, report);
  printRun(dir, report);
  return report;
}

function verify(dir) {
  const report = readJson(dir, ARTIFACTS.report);
  const problems = [];
  if (report.fixture.sha256 !== sha256(fixtureText)) problems.push('fixture changed since the report was generated');

  const verification = verifyArtifacts(dir);
  const recomputed = [...artifactChecks(verification), ...tamperChecks(dir, readJson(dir, ARTIFACTS.receipts), readJson(dir, ARTIFACTS.nodes))];
  for (const check of recomputed) {
    if (check.status !== 'pass') problems.push(`${check.id}: ${check.title}`);
    const recorded = report.checks.find((entry) => entry.id === check.id);
    if (!recorded || recorded.status !== check.status) problems.push(`${check.id}: report says ${recorded?.status ?? 'missing'}, recomputed ${check.status}`);
  }
  if (digestOf(report.fixture.sha256, report.cases, report.checks) !== report.deterministicDigest) {
    problems.push('report digest does not match its cases and checks');
  }

  console.log(bold('Independent verification of recorded artifacts'));
  console.log(`  ${dim('directory')}  ${toPosix(relative(repoRoot, dir))}`);
  console.log(`  ${dim('recomputed')} ${recomputed.length} checks from ${Object.values(ARTIFACTS).join(', ')}`);
  if (problems.length > 0) {
    for (const problem of problems) console.log(`  ${STATUS_LABEL.fail}  ${problem}`);
    console.log(`${bold('Result')}  ${red('verification failed')}`);
    return false;
  }
  console.log(`  ${STATUS_LABEL.pass}  receipts, ledger chain, evidence nodes and report digest all verify`);
  console.log(`${bold('Result')}  ${green('verified')}  ${dim(`digest ${report.deterministicDigest.slice(0, 12)}`)}`);
  return true;
}

function toPosix(path) {
  return path.split(sep).join('/');
}

function printRun(dir, report) {
  const short = (hash) => hash.slice(0, 12);
  const commit = report.commit.sha === 'unknown'
    ? 'unknown'
    : `${report.commit.sha.slice(0, 8)} ${report.commit.worktreeClean ? '(clean)' : '(uncommitted changes)'}`;
  console.log(bold('GRC_Claw demo: approval boundary and evidence chain'));
  console.log(dim('Offline, synthetic fixture. No real tool, model or external service is called.'));
  console.log('');
  console.log(`${dim('commit ')}  ${commit}    ${dim('node')} ${report.environment.node} ${dim(`${report.environment.platform}/${report.environment.arch}`)}`);
  console.log(`${dim('fixture')}  ${report.fixture.id} v${report.fixture.version}    ${dim('sha256')} ${short(report.fixture.sha256)}`);

  report.cases.forEach((c, index) => {
    const v = report.verification.cases[index];
    console.log('');
    console.log(bold(`[${index + 1}/${report.cases.length}] ${c.tool} (${c.tier})`));
    console.log(`  ${dim('policy   ')}  ${c.outcome} · ${c.reason}`);
    const boundary = c.boundaryState === 'interrupt'
      ? `interrupt · waiting for human approval of receipt ${short(c.receiptHash)}`
      : c.boundaryState;
    console.log(`  ${dim('boundary ')}  ${boundary}`);
    console.log(`  ${dim('execution')}  ${c.toolInvoked ? 'tool invoked (simulated)' : 'tool never invoked'}`);
    console.log(`  ${dim('ledger   ')}  ${v.ledgerStates.join(' -> ')}`);
    console.log(`  ${dim('receipt  ')}  ${short(c.receiptHash)} ${v.receiptVerified ? green('verifies') : red('does not verify')}`);
    console.log(`  ${dim('evidence ')}  node ${short(c.nodeObjectHash)} ${v.nodeHashRecomputed && v.nodeBoundToReceipt ? green('bound to receipt') : red('not bound')}`);
  });

  const byId = Object.fromEntries(report.checks.map((check) => [check.id, check]));
  const allCases = (suffix) => report.checks.filter((check) => check.id.endsWith(suffix));
  const line = (status, title, detail = '') =>
    console.log(`  ${STATUS_LABEL[status]}  ${detail ? `${title.padEnd(48)} ${dim(detail)}` : title}`);
  const combined = (list) => (list.every((check) => check.status === 'pass') ? 'pass' : 'fail');
  const passed = (list) => `${list.filter((check) => check.status === 'pass').length}/${list.length}`;

  console.log('');
  console.log(bold(`Independent verification ${dim(`(re-read from ${toPosix(relative(repoRoot, dir))})`)}`));
  line(combined(allCases('.receipt')), 'receipts verify', passed(allCases('.receipt')));
  line(byId['ledger.chain'].status, 'ledger hash chain verifies', `${report.verification.chain.checked} events`);
  line(combined(allCases('.evidence')), 'evidence nodes recompute and bind to receipts', passed(allCases('.evidence')));
  line(combined(allCases('.ledger')), 'ledger states match the fixture', passed(allCases('.ledger')));
  console.log(bold('Tamper checks'));
  for (const id of ['tamper.receipt-outcome', 'tamper.evidence-controls', 'tamper.ledger-event']) line(byId[id].status, byId[id].title);
  console.log(bold('Not applicable'));
  line(byId['approval.resume'].status, byId['approval.resume'].title, 'resume path not implemented yet');

  const s = report.summary;
  console.log('');
  console.log(`${bold('Result')}  ${s.pass} pass · ${s.fail} fail · ${s.unknown} unknown · ${s.not_applicable} not applicable    ${dim(`digest ${short(report.deterministicDigest)}`)}`);
  console.log(dim(`Artifacts: ${toPosix(relative(repoRoot, dir))}/{${Object.values(ARTIFACTS).join(', ')}}`));
}

const [command, outputArg] = process.argv.slice(2);
if (command !== 'run' && command !== 'verify') {
  console.error('Usage: node --import tsx examples/approval-evidence-chain/demo.mjs <run|verify> [output-directory]');
  process.exitCode = 2;
} else {
  const dir = resolve(outputArg ?? join(here, 'out'));
  try {
    const ok = command === 'run' ? run(dir).summary.fail === 0 : verify(dir);
    process.exitCode = ok ? 0 : 1;
  } catch (error) {
    console.error(`approval-evidence-chain ${command} failed: ${error.message}`);
    process.exitCode = 1;
  }
}
