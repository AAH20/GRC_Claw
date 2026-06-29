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

const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');
const exists = (relativePath) => fs.existsSync(path.join(root, relativePath));

const packageJson = JSON.parse(read('package.json'));
const readme = read('README.md');
const gatewayServer = read('packages/gateway/src/server.ts');
const agentDispatch = read('packages/gateway/src/agent-dispatch.ts');

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
const evidenceGraphRoutes = [...gatewayServer.matchAll(/['"`](\/api\/evidence-graph[^'"`]*)['"`]/g)]
  .map((match) => match[1])
  .filter((route, index, all) => all.indexOf(route) === index)
  .sort();

const requiredPackages = [
  'evidence-graph',
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
    id: 'phase36_readme_present',
    ok: readme.includes('Phase 36 graph-first review'),
    remediation: 'Keep the Phase 36 graph-first moat review in README.md.',
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
    ok: evidenceGraphRoutes.length >= 4,
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
];

const failures = checks.filter((check) => !check.ok);
const summary = {
  ok: failures.length === 0,
  checkedAt: new Date().toISOString(),
  packages: packages.length,
  gatewayTools: gatewayTools.length,
  evidenceGraphTools,
  evidenceGraphRoutes,
  checks: checks.map(({ id, ok, remediation }) => ({ id, ok, remediation: ok ? undefined : remediation })),
};

if (process.argv.includes('--json')) {
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
} else {
  console.log('GRC_Claw graph/proof coverage gate');
  console.log(`- packages: ${summary.packages}`);
  console.log(`- gateway tools: ${summary.gatewayTools}`);
  console.log(`- evidence graph tools: ${summary.evidenceGraphTools.join(', ')}`);
  console.log(`- evidence graph routes: ${summary.evidenceGraphRoutes.join(', ')}`);
  console.log('');
  for (const check of summary.checks) {
    console.log(`${check.ok ? '✓' : '✗'} ${check.id}`);
    if (!check.ok) console.log(`  remediation: ${check.remediation}`);
  }
}

if (failures.length > 0) {
  process.exitCode = 1;
}
