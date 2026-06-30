#!/usr/bin/env node
/**
 * @domain trust-engineering
 * @layer release-gate
 * @summary Verifies that GRC_Claw keeps the graph/proof primitives required for proof-native GRC.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '..');
const historyPath = path.join(root, 'docs/graph-proof-coverage-history.json');

const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');
const exists = (relativePath) => fs.existsSync(path.join(root, relativePath));
const unique = (items) => [...new Set(items)].sort();

const packageJson = JSON.parse(read('package.json'));
const readme = read('README.md');
const gatewayServer = read('packages/gateway/src/server.ts');
const agentDispatch = read('packages/gateway/src/agent-dispatch.ts');

const readTree = (relativePath) => {
  const absolutePath = path.join(root, relativePath);
  if (!fs.existsSync(absolutePath)) return '';
  const sourceExtensions = new Set(['.md', '.json', '.ts', '.tsx', '.js', '.mjs', '.yml', '.yaml']);
  const chunks = [];
  const walk = (currentPath) => {
    const stat = fs.statSync(currentPath);
    if (stat.isDirectory()) {
      for (const entry of fs.readdirSync(currentPath)) {
        if (['dist', 'node_modules', '.turbo'].includes(entry)) continue;
        walk(path.join(currentPath, entry));
      }
      return;
    }
    if (!sourceExtensions.has(path.extname(currentPath))) return;
    chunks.push(fs.readFileSync(currentPath, 'utf8'));
  };
  walk(absolutePath);
  return chunks.join('\n');
};

const listWorkspacePackages = () => {
  const packagesDir = path.join(root, 'packages');
  return fs
    .readdirSync(packagesDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .filter((entry) => exists(`packages/${entry.name}/package.json`))
    .map((entry) => entry.name)
    .sort();
};

const extractCaseTools = (source) => {
  const tools = new Set();
  const pattern = /case\s+['"`]([^'"`]+)['"`]\s*:/g;
  let match;
  while ((match = pattern.exec(source)) !== null) {
    tools.add(match[1]);
  }
  return [...tools].sort();
};

const packages = listWorkspacePackages();
const gatewayTools = extractCaseTools(agentDispatch);
const evidenceGraphTools = gatewayTools.filter((tool) => tool.startsWith('evidence_graph.'));
const allHttpRoutes = unique(
  [...gatewayServer.matchAll(/['"`](\/api\/[^'"`]*)['"`]/g)].map((match) => match[1])
);
const evidenceGraphRoutes = allHttpRoutes
  .filter((route) => route.startsWith('/api/evidence-graph'))
  .sort();

const packageSource = (packageName) => readTree(`packages/${packageName}`);
const copilotSource = [
  packageSource('compliance-copilot'),
  packageSource('natural-language-compliance'),
  packageSource('compliance-knowledge-graph'),
].join('\n');
const marketplaceSource = [
  readme,
  packageSource('compliance-marketplace'),
  packageSource('compliance-automation-marketplace'),
  packageSource('integration-marketplace'),
  packageSource('trust-marketplace'),
].join('\n');
const procurementSource = [
  readme,
  packageSource('ai-governance'),
  packageSource('aims'),
  packageSource('board-reporting'),
  packageSource('oscal'),
  readTree('packages/agent-runtime/scripts'),
].join('\n');
const verifierSource = [
  readme,
  gatewayServer,
  packageSource('trust-center'),
  packageSource('zero-trust-audit'),
  packageSource('zk-compliance'),
  packageSource('evidence'),
].join('\n');
const benchmarkSource = [
  readme,
  gatewayServer,
  packageSource('predictive-compliance'),
  packageSource('compliance-intelligence-api'),
  packageSource('real-time-compliance-monitor'),
  packageSource('continuous-trust-engine'),
].join('\n');
const trustTransactionSource = [
  readme,
  packageSource('trust-transaction'),
  packageSource('evidence-graph'),
  packageSource('evidence'),
].join('\n');

const coverageTarget = (id, ok, evidence, remediation) => ({
  id,
  ok,
  evidence,
  remediation: ok ? undefined : remediation,
});

const routeTarget = (route) =>
  coverageTarget(
    `route:${route}`,
    allHttpRoutes.includes(route),
    route,
    `Add or preserve the ${route} proof route in packages/gateway/src/server.ts.`
  );

const toolTarget = (tool) =>
  coverageTarget(
    `tool:${tool}`,
    gatewayTools.includes(tool),
    tool,
    `Add or preserve the ${tool} gateway/MCP tool in packages/gateway/src/agent-dispatch.ts.`
  );

const prefixToolTarget = (id, prefix, minimum) => {
  const matches = gatewayTools.filter((tool) => tool.startsWith(prefix));
  return coverageTarget(
    id,
    matches.length >= minimum,
    `${matches.length}/${minimum} tools with prefix ${prefix}`,
    `Expected at least ${minimum} gateway tools with prefix ${prefix}.`
  );
};

const packageTarget = (packageName) =>
  coverageTarget(
    `package:${packageName}`,
    packages.includes(packageName),
    packageName,
    `Add or restore packages/${packageName}.`
  );

const tokenTarget = (id, source, tokens, minimum = tokens.length) => {
  const matched = tokens.filter((token) => source.includes(token));
  return coverageTarget(
    id,
    matched.length >= minimum,
    `${matched.length}/${tokens.length}: ${matched.join(', ') || 'none'}`,
    `Expected at least ${minimum}/${tokens.length} token(s): ${tokens.join(', ')}.`
  );
};

const coverageGroup = (id, minimumRatio, targets) => {
  const covered = targets.filter((target) => target.ok).length;
  const total = targets.length;
  const ratio = total === 0 ? 1 : covered / total;
  return {
    id,
    minimumRatio,
    covered,
    total,
    ratio: Number(ratio.toFixed(3)),
    ok: ratio >= minimumRatio,
    targets,
  };
};

const coverageGroups = [
  coverageGroup('route_to_proof', 0.85, [
    routeTarget('/api/evidence-graph'),
    routeTarget('/api/evidence-graph/summary'),
    routeTarget('/api/evidence-graph/nodes'),
    routeTarget('/api/evidence-graph/edges'),
    routeTarget('/api/assurance'),
    routeTarget('/api/action-ledger'),
    routeTarget('/api/evidence/collect'),
    routeTarget('/api/evidence/inventory'),
    routeTarget('/api/agent/invoke'),
  ]),
  coverageGroup('tool_to_policy', 0.8, [
    prefixToolTarget('tools:evidence_graph', 'evidence_graph.', 5),
    toolTarget('evidence.generate_assurance_envelope'),
    toolTarget('agent.invoke'),
    toolTarget('identity.authorize_tool_access'),
    prefixToolTarget('tools:policy', 'policy.', 3),
    prefixToolTarget('tools:audit', 'audit.', 2),
    prefixToolTarget('tools:risk', 'risk.', 3),
    prefixToolTarget('tools:trust', 'trust.', 3),
    toolTarget('a2z.sync_to_private'),
  ]),
  coverageGroup('copilot_to_evidence', 0.75, [
    packageTarget('compliance-copilot'),
    packageTarget('natural-language-compliance'),
    packageTarget('compliance-knowledge-graph'),
    tokenTarget('copilot:control_mapping', copilotSource, ['control', 'framework', 'map'], 2),
    tokenTarget('copilot:evidence_response', copilotSource, ['evidence', 'confidence', 'risk'], 2),
    tokenTarget('copilot:proof_path_roadmap', readme, ['Proof-native GRC Copilot', 'missing-evidence', 'verifier-room export'], 2),
  ]),
  coverageGroup('marketplace_to_signed_pack', 0.75, [
    packageTarget('compliance-marketplace'),
    packageTarget('compliance-automation-marketplace'),
    packageTarget('integration-marketplace'),
    packageTarget('trust-marketplace'),
    tokenTarget('marketplace:signed_supply_chain', marketplaceSource, ['signed', 'provenance', 'semantic versioning'], 2),
    tokenTarget('marketplace:revenue_trust', marketplaceSource, ['revenue share', 'verifier', 'rating'], 2),
  ]),
  coverageGroup('procurement_to_export', 0.75, [
    tokenTarget('procurement:framework_wedge', procurementSource, ['CMMC', 'NIST 800-171', 'ISO 42001'], 3),
    tokenTarget('procurement:packet_artifacts', procurementSource, ['SSP', 'POA&M', 'SBOM', 'AI-BOM'], 3),
    tokenTarget('procurement:export_modes', procurementSource, ['auditor', 'board', 'government buyer', 'MSP/vCISO'], 3),
    packageTarget('ai-governance'),
    packageTarget('aims'),
    packageTarget('board-reporting'),
    packageTarget('oscal'),
  ]),
  coverageGroup('verifier_export', 0.75, [
    routeTarget('/api/assurance'),
    packageTarget('trust-center'),
    packageTarget('zero-trust-audit'),
    packageTarget('zk-compliance'),
    tokenTarget('verifier:rooms', verifierSource, ['verifier', 'redacted evidence', 'signed receipts'], 2),
    tokenTarget('verifier:exports', verifierSource, ['export', 'proof', 'assurance'], 2),
  ]),
  coverageGroup('benchmark_intelligence', 0.7, [
    packageTarget('predictive-compliance'),
    packageTarget('compliance-intelligence-api'),
    packageTarget('real-time-compliance-monitor'),
    packageTarget('continuous-trust-engine'),
    tokenTarget('benchmark:outcomes', benchmarkSource, ['benchmark', 'audit cycle time', 'remediation latency'], 2),
    tokenTarget('benchmark:signals', benchmarkSource, ['evidence freshness', 'policy denial', 'verifier acceptance'], 2),
  ]),
  coverageGroup('trust_transaction_network', 0.8, [
    packageTarget('trust-transaction'),
    tokenTarget('trust_transaction:envelope', trustTransactionSource, ['TrustTransactionEnvelope', 'transactionHash', 'dataBoundary'], 3),
    tokenTarget('trust_transaction:policy', trustTransactionSource, ['sandboxPolicy', 'approvalThreshold', 'rollbackPlanId'], 3),
    tokenTarget('trust_transaction:evidence', trustTransactionSource, ['evidenceHash', 'graphObjectHash', 'controlIds'], 3),
    tokenTarget('trust_transaction:verifier', trustTransactionSource, ['verifier_receipt', 'receiptHash', 'verifier_room'], 2),
    tokenTarget('trust_transaction:copilot_guardrail', trustTransactionSource, ['copilot_answer', 'missing_evidence_task', 'copilot_answer_missing_proof'], 3),
    tokenTarget('trust_transaction:exports', trustTransactionSource, ['procurement_packet', 'benchmark_api', 'diligence_api'], 3),
  ]),
];

const coverageChecks = coverageGroups.map((group) => ({
  id: `${group.id}_coverage`,
  ok: group.ok,
  remediation: `${group.id} coverage ${Math.round(group.ratio * 100)}% is below required ${Math.round(
    group.minimumRatio * 100
  )}%.`,
}));

const evidenceGraphRoutesLegacy = [...gatewayServer.matchAll(/['"`](\/api\/evidence-graph[^'"`]*)['"`]/g)]
  .map((match) => match[1])
  .filter((route, index, all) => all.indexOf(route) === index)
  .sort();

const requiredPackages = [
  'evidence-graph',
  'trust-transaction',
  'gateway',
  'mcp-server',
  'agent-runtime',
  'compliance-knowledge-graph',
  'compliance-marketplace',
  'compliance-automation-marketplace',
  'predictive-compliance',
  'zero-trust-audit',
  'natural-language-compliance',
  'quantum-resistant-crypto',
];

const checks = [
  {
    id: 'script_registered',
    ok: packageJson.scripts?.['graph:coverage'] === 'node scripts/graph-proof-coverage.mjs',
    remediation: 'Add "graph:coverage": "node scripts/graph-proof-coverage.mjs" to package.json.',
  },
  {
    id: 'phase38_readme_present',
    ok: readme.includes('Phase 38 graph-first category control'),
    remediation: 'Keep the Phase 38 Trust Transaction Network roadmap in README.md.',
  },
  {
    id: 'required_packages_present',
    ok: requiredPackages.every((pkg) => packages.includes(pkg)),
    remediation: `Missing required package(s): ${requiredPackages.filter((pkg) => !packages.includes(pkg)).join(', ')}`,
  },
  {
    id: 'gateway_evidence_graph_imported',
    ok: gatewayServer.includes('@grc-claw/evidence-graph') && agentDispatch.includes('@grc-claw/evidence-graph'),
    remediation: 'Gateway server and agent dispatch must import @grc-claw/evidence-graph.',
  },
  {
    id: 'http_evidence_graph_routes',
    ok: evidenceGraphRoutesLegacy.length >= 4,
    remediation: 'Expose /api/evidence-graph, /summary, /nodes, and /edges routes.',
  },
  {
    id: 'mcp_evidence_graph_tools',
    ok: evidenceGraphTools.length >= 5,
    remediation: 'Expose evidence_graph.get, get_summary, get_nodes, get_edges, and get_recommendations tools.',
  },
  {
    id: 'action_ledger_lifecycle',
    ok: ['recordIntent', 'recordDecision', 'recordResult'].every((token) => gatewayServer.includes(token)),
    remediation: 'Gateway agent actions must record intent, decision, and result events.',
  },
  {
    id: 'assurance_envelope_persistence',
    ok: ['createAssuranceEnvelope', 'persistAssuranceEnvelope', 'assuranceReceipt'].every((token) => gatewayServer.includes(token)),
    remediation: 'Gateway must persist assurance envelopes and return assurance receipts.',
  },
  {
    id: 'agent_assurance_tool',
    ok: gatewayTools.includes('evidence.generate_assurance_envelope'),
    remediation: 'Agent dispatch must expose evidence.generate_assurance_envelope.',
  },
  {
    id: 'defense_procurement_roadmap',
    ok: ['CMMC', 'NIST 800-171', 'ISO 42001'].every((token) => readme.includes(token)),
    remediation: 'README roadmap must keep the defense procurement cockpit wedge explicit.',
  },
  {
    id: 'trust_transaction_schema_package',
    ok:
      packages.includes('trust-transaction') &&
      trustTransactionSource.includes('createTrustTransaction') &&
      trustTransactionSource.includes('verifyTrustTransaction') &&
      trustTransactionSource.includes('redactTrustTransactionForSharing'),
    remediation: 'Trust Transaction schema, hashing, validation, and redaction package must remain available.',
  },
  {
    id: 'graph_coverage_history_baseline',
    ok: exists('docs/graph-proof-coverage-history.json'),
    remediation: 'Keep docs/graph-proof-coverage-history.json so CI can compare graph coverage trends.',
  },
  ...coverageChecks,
];

const failures = checks.filter((check) => !check.ok);
const summary = {
  ok: failures.length === 0,
  checkedAt: new Date().toISOString(),
  packages: packages.length,
  gatewayTools: gatewayTools.length,
  evidenceGraphTools,
  evidenceGraphRoutes,
  coverageGroups: coverageGroups.map((group) => ({
    id: group.id,
    minimumRatio: group.minimumRatio,
    covered: group.covered,
    total: group.total,
    ratio: group.ratio,
    ok: group.ok,
    missingTargets: group.targets
      .filter((target) => !target.ok)
      .map(({ id, evidence, remediation }) => ({ id, evidence, remediation })),
  })),
  checks: checks.map(({ id, ok, remediation }) => ({ id, ok, remediation: ok ? undefined : remediation })),
};

const loadHistory = () => {
  if (!fs.existsSync(historyPath)) return [];
  const parsed = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
  return Array.isArray(parsed) ? parsed : [];
};

const compactSummary = (input) => ({
  checkedAt: input.checkedAt,
  ok: input.ok,
  packages: input.packages,
  gatewayTools: input.gatewayTools,
  coverageGroups: input.coverageGroups.map(({ id, covered, total, ratio, ok }) => ({ id, covered, total, ratio, ok })),
});

const latestHistory = loadHistory().at(-1);
const coverageTrend = summary.coverageGroups.map((group) => {
  const previous = latestHistory?.coverageGroups?.find?.((item) => item.id === group.id);
  return {
    id: group.id,
    ratio: group.ratio,
    previousRatio: previous?.ratio,
    delta: previous ? Number((group.ratio - previous.ratio).toFixed(3)) : undefined,
  };
});

summary.coverageTrend = coverageTrend;

if (process.argv.includes('--json')) {
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
} else {
  console.log('GRC_Claw graph/proof coverage gate');
  console.log(`- packages: ${summary.packages}`);
  console.log(`- gateway tools: ${summary.gatewayTools}`);
  console.log(`- evidence graph tools: ${summary.evidenceGraphTools.join(', ')}`);
  console.log(`- evidence graph routes: ${summary.evidenceGraphRoutes.join(', ')}`);
  console.log('');
  console.log('Coverage ratios:');
  for (const group of summary.coverageGroups) {
    const trend = summary.coverageTrend.find((item) => item.id === group.id);
    const trendText =
      trend?.delta === undefined
        ? ''
        : `, trend ${trend.delta > 0 ? '+' : ''}${Math.round(trend.delta * 100)} pts vs baseline`;
    console.log(
      `- ${group.ok ? '✓' : '✗'} ${group.id}: ${group.covered}/${group.total} (${Math.round(
        group.ratio * 100
      )}%, min ${Math.round(group.minimumRatio * 100)}%${trendText})`
    );
    for (const missing of group.missingTargets) {
      console.log(`  missing ${missing.id}: ${missing.remediation}`);
    }
  }
  console.log('');
  for (const check of summary.checks) {
    console.log(`${check.ok ? '✓' : '✗'} ${check.id}`);
    if (!check.ok) console.log(`  remediation: ${check.remediation}`);
  }
}

if (process.argv.includes('--write-history')) {
  const history = loadHistory();
  history.push(compactSummary(summary));
  fs.mkdirSync(path.dirname(historyPath), { recursive: true });
  fs.writeFileSync(historyPath, `${JSON.stringify(history, null, 2)}\n`);
  if (!process.argv.includes('--json')) {
    console.log('');
    console.log(`✓ graph_coverage_history_written ${path.relative(root, historyPath)}`);
  }
}

if (failures.length > 0) {
  process.exitCode = 1;
}
