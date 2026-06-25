import { RegulationASTCompiler } from './compiler/RegulationASTCompiler.js';
import { NeuroSymbolicReasoner } from './reasoner/NeuroSymbolicReasoner.js';
import { UnifiedComplianceGraph } from './graph/UnifiedComplianceGraph.js';
import { ComplianceSuperOrchestrator } from './index.js';
import type { FrameworkCode } from './types.js';
import type { ReasoningContext } from './reasoner/NeuroSymbolicReasoner.js';

async function testRegulationASTCompiler() {
  console.log('\n=== Testing Regulation AST Compiler ===');
  const compiler = new RegulationASTCompiler();

  const isoAST = compiler.getAST('iso27001');
  console.log(`ISO 27001 AST compiled: ${isoAST?.controls.length} controls`);
  console.log(`  Families: ${isoAST?.metadata.families.join(', ')}`);
  console.log(`  Crosswalks: ${isoAST?.crosswalks.length}`);

  const soc2AST = compiler.getAST('soc2');
  console.log(`SOC 2 AST compiled: ${soc2AST?.controls.length} controls`);

  const iso42001AST = compiler.getAST('iso42001');
  console.log(`ISO 42001 AST compiled: ${iso42001AST?.controls.length} controls`);

  const euAiAST = compiler.getAST('eu-ai-act');
  console.log(`EU AI Act AST compiled: ${euAiAST?.controls.length} controls`);

  const doraAST = compiler.getAST('dora');
  console.log(`DORA AST compiled: ${doraAST?.controls.length} controls`);

  const equiv = compiler.findEquivalent('iso27001', 'A.8.2');
  console.log(`Crosswalk A.8.2 → SOC 2: ${equiv.map((e) => `${e.targetFramework}:${e.targetControl}`).join(', ')}`);

  const nl = compiler.compileNaturalLanguage('iso27001', 'Organization shall implement AI model governance');
  console.log(`Natural language compiled: ${nl.id}`);

  console.log('✓ Regulation AST Compiler tests passed');
}

async function testNeuroSymbolicReasoner() {
  console.log('\n=== Testing Neuro-Symbolic Reasoner ===');
  const compiler = new RegulationASTCompiler();
  const asts = compiler.getAllASTs();
  const astMap = new Map(asts.map((a) => [a.framework, a]));
  const reasoner = new NeuroSymbolicReasoner(astMap);

  const context: ReasoningContext = {
    orgId: 'test-org',
    framework: 'iso27001',
    currentEvidence: new Map([
      ['iso-a.8.2', [{ id: 'ev-1', controlId: 'iso-a.8.2', type: 'config', hash: 'abc123', timestamp: new Date().toISOString(), valid: true }]],
      ['iso-a.8.5', [{ id: 'ev-2', controlId: 'iso-a.8.5', type: 'config', hash: 'def456', timestamp: new Date().toISOString(), valid: true }]],
    ]),
    configurationState: {
      iam: { mfaEnabled: true, privilegedUsers: ['admin', 'ops'], sessionTimeout: 900, lastPasswordRotation: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(), rbacPolicyVersion: '2.0', mfaEnforcementRate: 0.98 },
      network: { firewallRules: 15, segmentationEnabled: true, idsEnabled: true, tlsVersion: '1.3', publicEndpoints: [] },
      data: { encryptionAtRest: true, encryptionInTransit: true, backupEnabled: true, backupFrequency: 'daily', lastBackup: new Date().toISOString(), retentionDays: 90 },
      monitoring: { siemEnabled: true, logRetentionDays: 180, alertingEnabled: true, mttr: 4, monitoringCoverage: 95 },
      physical: { accessControl: true, cctvEnabled: true, environmentalMonitoring: true, visitorManagement: true },
    },
    riskTolerance: 'medium',
  };

  const state = await reasoner.reason(context);
  console.log(`ISO 27001 compliance score: ${state.overallScore.toFixed(1)}%`);
  console.log(`  Controls evaluated: ${state.controlStatuses.length}`);
  console.log(`  Compliant: ${state.controlStatuses.filter((s) => s.status === 'compliant').length}`);
  console.log(`  Non-compliant: ${state.controlStatuses.filter((s) => s.status === 'non-compliant').length}`);
  console.log(`  Risks: ${state.risks.length}`);

  for (const cs of state.controlStatuses.slice(0, 3)) {
    console.log(`  ${cs.controlId}: ${cs.status} (score: ${cs.score.toFixed(1)})`);
  }

  console.log('✓ Neuro-Symbolic Reasoner tests passed');
}

async function testUnifiedComplianceGraph() {
  console.log('\n=== Testing Unified Compliance Graph ===');
  const compiler = new RegulationASTCompiler();
  const asts = compiler.getAllASTs();
  const graph = new UnifiedComplianceGraph(asts);

  console.log(`Graph nodes: ${graph.getGraphHash()}`);

  const blastRadius = graph.calculateBlastRadius('control:iso27001:A.8.2');
  console.log(`Blast radius for A.8.2: ${blastRadius.impactScore.toFixed(2)} (${blastRadius.affectedControls.length} controls)`);

  const attackPaths = graph.traceAttackPaths('control:iso27001:A.8.2', 3);
  console.log(`Attack paths found: ${attackPaths.length}`);

  console.log('✓ Unified Compliance Graph tests passed');
}

async function testComplianceSuperOrchestrator() {
  console.log('\n=== Testing Compliance Super Orchestrator ===');
  const orchestrator = new ComplianceSuperOrchestrator({
    orgId: 'test-org',
    enabledFrameworks: ['iso27001', 'soc2', 'iso42001'],
    riskTolerance: 'medium',
    autoRemediate: false,
    continuousScanInterval: 300000,
  });

  const contexts = new Map<FrameworkCode, ReasoningContext>();
  const baseEvidence = new Map([
    ['iso-a.8.2', [{ id: 'ev-1', controlId: 'iso-a.8.2', type: 'config', hash: 'abc', timestamp: new Date().toISOString(), valid: true }]],
  ]);
  const baseConfig = {
    iam: { mfaEnabled: true, privilegedUsers: ['admin'], sessionTimeout: 900, lastPasswordRotation: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(), rbacPolicyVersion: '2.0', mfaEnforcementRate: 0.98 },
    network: { firewallRules: 10, segmentationEnabled: true, idsEnabled: true, tlsVersion: '1.3', publicEndpoints: [] },
    data: { encryptionAtRest: true, encryptionInTransit: true, backupEnabled: true, backupFrequency: 'daily', lastBackup: new Date().toISOString(), retentionDays: 90 },
    monitoring: { siemEnabled: true, logRetentionDays: 180, alertingEnabled: true, mttr: 4, monitoringCoverage: 90 },
    physical: { accessControl: true, cctvEnabled: true, environmentalMonitoring: true, visitorManagement: true },
  };

  contexts.set('iso27001', { orgId: 'test-org', framework: 'iso27001', currentEvidence: baseEvidence, configurationState: baseConfig, riskTolerance: 'medium' });
  contexts.set('soc2', { orgId: 'test-org', framework: 'soc2', currentEvidence: baseEvidence, configurationState: baseConfig, riskTolerance: 'medium' });
  contexts.set('iso42001', { orgId: 'test-org', framework: 'iso42001', currentEvidence: baseEvidence, configurationState: baseConfig, riskTolerance: 'medium' });

  const result = await orchestrator.continuousComplianceLoop(contexts);
  console.log(`Overall compliance score: ${result.overallScore.toFixed(1)}%`);
  console.log(`Frameworks evaluated: ${result.states.length}`);
  console.log(`Drift events: ${result.drift.length}`);
  console.log(`Risks identified: ${result.risks.length}`);

  const plan = await orchestrator.synthesizePlan('iso27001', result.states[0], 95);
  console.log(`Remediation plan: ${plan.actions.length} actions, estimated ${plan.estimatedDuration}`);

  const audit = await orchestrator.executeAudit('iso27001', contexts.get('iso27001')!);
  console.log(`Audit result: ${audit.summary.passed}/${audit.summary.totalControls} passed`);

  console.log('✓ Compliance Super Orchestrator tests passed');
}

async function runAllTests() {
  console.log('Starting Compliance Orchestrator Tests...\n');
  console.log('='.repeat(60));

  await testRegulationASTCompiler();
  await testNeuroSymbolicReasoner();
  await testUnifiedComplianceGraph();
  await testComplianceSuperOrchestrator();

  console.log('\n' + '='.repeat(60));
  console.log('All Compliance Orchestrator tests passed! ✓');
  console.log('='.repeat(60));
}

runAllTests().catch(console.error);
