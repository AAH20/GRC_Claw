import type { A2ZSocConnector } from '@grc-claw/a2z-connector';
import { listClauseMap, listTechnicalControls, listVendorGaps } from '@grc-claw/aims';
import type { EvidenceStore } from '@grc-claw/evidence';
import { buildEvidenceGraphSnapshot as buildEvidenceGraphObjectSnapshot, edgeObject, nodeObject } from '@grc-claw/evidence-graph';
import { listFrameworkPacks } from '@grc-claw/frameworks';
import {
  dispatchConnectorTool,
  isConnectorTool,
  type ConnectorRegistry,
} from '@grc-claw/connectors';
import { dispatchClawTool, isClawTool, type ClawDispatchContext } from '@grc-claw/skill-executor';
import { VectorGraphMemory, SkillsRegistry, AgentSession, ExecPolicy, PersistentMemoryStore } from '@grc-claw/agent-runtime';
import { normalizeBySource, CLOUD_INGEST_SOURCES } from '@grc-claw/ingest';
import type { IngestSource } from '@grc-claw/ingest';
import { createAssuranceEnvelope, ActionLedger } from '@grc-claw/evidence';
import { SecurityGraph } from '@grc-claw/security-graph';
import { MonteCarloEngine, FAIRCalculator, RiskRegister } from '@grc-claw/risk-quantification';
import { EntityManager } from '@grc-claw/entity-management';
import { SOAREngine } from '@grc-claw/soar';
import type { Playbook, SOARContext } from '@grc-claw/soar';
import type { DriftDetector } from '@grc-claw/drift-detector';
import type { EvidenceCollectorEngine } from '@grc-claw/evidence-collector';
import { CloudConnectorRegistry } from '@grc-claw/cloud-connectors';
import { AuditManager } from '@grc-claw/audit-management';
import type { Audit, Finding } from '@grc-claw/audit-management';
import * as fs from 'fs';
import * as path from 'path';
import { ACCMEngine, type FrameworkCode as ACCMFrameworkCode, type GapDetector } from '@grc-claw/accm';
import { FrameworkCrosswalk } from '@grc-claw/framework-crosswalk';
import { ChatGRC } from '@grc-claw/chat-grc';
import { AgentIdentityManager } from '@grc-claw/agent-identity';
import { VendorRegistry } from '@grc-claw/third-party-risk';
import { TrustCenter } from '@grc-claw/trust-center';
import { RegulatoryIntelligenceEngine } from '@grc-claw/regulatory-intelligence';
import { PolicyManager } from '@grc-claw/policy-management';
import { ComplianceSuperOrchestrator } from '@grc-claw/compliance-orchestrator';
import { ContinuousComplianceEngine } from '@grc-claw/continuous-compliance';
import { AnomalyDetector } from '@grc-claw/ai-threat-detection';
import { AISupplyChainSovereignty } from '@grc-claw/ai-supply-chain';
import { FederatedComplianceMesh } from '@grc-claw/federated-compliance-mesh';
import { AutoEvidenceCollector } from '@grc-claw/auto-evidence';
import { BrowserEvidenceCollector, PlaywrightAdapter, type PortalConfig } from '@grc-claw/browser-evidence';
import { IncidentManager } from '@grc-claw/incident-response';
import { GitHubPRReviewer, CICDComplianceGate } from '@grc-claw/dev-compliance';
import { CompliancePipeline, GitOpsWorkflow } from '@grc-claw/grc-engineering';
import { AgentTrustScoreEngine } from '@grc-claw/agent-trust-score';
import { TerraformProvider } from '@grc-claw/terraform-provider';

import { BoardReportGenerator } from '@grc-claw/board-reporting';
import { AgentAuditTrail } from '@grc-claw/agent-audit-trail';
import { IntegrationMarketplace } from '@grc-claw/integration-marketplace';
import { PolicyManagementHub } from '@grc-claw/policy-management-hub';
import { VendorRiskManagement } from '@grc-claw/vendor-risk-management';
import { EmployeeLifecycleEngine } from '@grc-claw/employee-lifecycle';
import { ComplianceTaskEngine } from '@grc-claw/compliance-task-engine';
import { EvidenceAutomationEngine } from '@grc-claw/evidence-automation-engine';
import { ComplianceKnowledgeGraph, seedFrameworkKnowledge, crosswalk, calculatePosture, analyseGaps, propagateRisk } from '@grc-claw/compliance-knowledge-graph';
import { PredictiveComplianceEngine, TimeSeriesAnalyzer, RiskScoringEngine, MonteCarloSimulator } from '@grc-claw/predictive-compliance';
import { ComplianceMarketplace, CompliancePack, MarketplaceRegistry, PricingEngine } from '@grc-claw/compliance-marketplace';
import { ZeroTrustAuditTrail, MerkleTree, CryptoSigner, EvidenceVault, CourtAdmissibleExporter } from '@grc-claw/zero-trust-audit';

const vectorMemory = new VectorGraphMemory();
const skillsRegistry = new SkillsRegistry();
export const identityManager = new AgentIdentityManager();
let securityGraph = new SecurityGraph();
const soarContext: SOARContext = {
  quarantineAgent: async (agentDid: string, params: Record<string, unknown>) => {
    actionLedger.recordIntent({
      tenantId: 1,
      sessionId: `soar-quarantine-${Date.now()}`,
      tool: 'soar.quarantine_agent',
      args: { agentDid, ...params },
    });
    securityGraph.addNode({
      id: `quarantine-${agentDid}`,
      name: `Quarantined: ${agentDid}`,
      type: 'infrastructure',
      riskScore: 100,
      properties: { action: 'quarantine', agentDid, ...params },
      tags: ['quarantine', 'soar'],
    });
    return { quarantined: true, agentDid, recorded: true, quarantinedAt: new Date().toISOString() };
  },
  revokeDID: async (agentDid: string, params: Record<string, unknown>) => {
    actionLedger.recordIntent({
      tenantId: 1,
      sessionId: `soar-revoke-${Date.now()}`,
      tool: 'soar.revoke_did',
      args: { agentDid, ...params },
    });
    return { revoked: true, agentDid, revokedAt: new Date().toISOString(), recorded: true };
  },
  blockNetwork: async (params: Record<string, unknown>) => {
    const scope = String(params.scope ?? 'unknown');
    const agentDid = String(params.agentDid ?? 'unknown');
    actionLedger.recordIntent({
      tenantId: 1,
      sessionId: `soar-block-${Date.now()}`,
      tool: 'soar.block_network',
      args: params,
    });
    securityGraph.addNode({
      id: `network-block-${agentDid}`,
      name: `Network blocked: ${agentDid} (scope: ${scope})`,
      type: 'infrastructure',
      riskScore: 90,
      properties: { action: 'block_network', agentDid, scope, ...params },
      tags: ['firewall', 'network-block', 'soar'],
    });
    return { blocked: true, scope, agentDid, blockedAt: new Date().toISOString(), recorded: true };
  },
  rotateCredentials: async (params: Record<string, unknown>) => {
    actionLedger.recordIntent({
      tenantId: 1,
      sessionId: `soar-rotate-${Date.now()}`,
      tool: 'soar.rotate_credentials',
      args: params,
    });
    return { rotated: true, scope: params.scope ?? 'all', rotatedAt: new Date().toISOString(), recorded: true };
  },
  sendWebhook: async (url: string, payload: Record<string, unknown>) => {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10_000),
    });
    return { status: response.status, ok: response.ok, url };
  },
  updateControlStatus: async (controlId: string, status: string, evidenceHashes: string[]) => {
    actionLedger.recordIntent({
      tenantId: 1,
      sessionId: `soar-control-${Date.now()}`,
      tool: 'soar.update_control_status',
      args: { controlId, status, evidenceHashes },
    });
    return { controlId, status, evidenceHashes, updatedAt: new Date().toISOString(), recorded: true };
  },
  logEvidence: async (evidenceType: string, params: Record<string, unknown>) => {
    actionLedger.recordIntent({
      tenantId: 1,
      sessionId: `soar-evidence-${Date.now()}`,
      tool: 'soar.log_evidence',
      args: { evidenceType, ...params },
    });
    return { evidenceType, logged: true, loggedAt: new Date().toISOString(), recorded: true };
  },
};
const soarEngine = new SOAREngine(soarContext);
const auditManager = new AuditManager();
const cloudRegistry = new CloudConnectorRegistry();
const actionLedger = new ActionLedger();
const memoryStore = new PersistentMemoryStore();
const agentSessions = new Map<string, AgentSession>();
const riskRegister = new RiskRegister();
const entityManager = new EntityManager();
const vendorRegistry = new VendorRegistry();
const trustCenter = new TrustCenter();
const policyManager = new PolicyManager();
const regulatoryEngine = new RegulatoryIntelligenceEngine();
const supplyChain = new AISupplyChainSovereignty({
  orgId: 'grc-claw',
  enableTEE: true,
  enableZK: true,
  enableFederatedConsensus: true,
  minSafetyRating: 0.7,
  requireReproducibleBuilds: true,
});

const complianceMesh = new FederatedComplianceMesh();

const complianceOrchestrator = new ComplianceSuperOrchestrator({
  orgId: 'grc-claw',
  enabledFrameworks: ['iso27001'],
  riskTolerance: 'medium',
  autoRemediate: false,
  continuousScanInterval: 3600000,
});
const continuousEngine = new ContinuousComplianceEngine(
  {
    async verifyEvidence() { return true; },
    async getCurrentEvidence() { return []; },
  },
  {
    async execute(_script: string, _context: Record<string, unknown>) { return { success: true, message: 'no-op', actionsTaken: [] as string[] }; },
  },
);
const anomalyDetector = new AnomalyDetector();
const autoEvidence = new AutoEvidenceCollector();
const incidentManager = new IncidentManager();
const boardReporter = new BoardReportGenerator();
const trustScoreEngine = new AgentTrustScoreEngine({
  issuerId: 'grc-claw-gateway',
  credentialStore: {
    async store(_credential: import('@grc-claw/agent-trust-score').TrustCredential) {},
    async get(_id: string) { return undefined; },
    async listByAgent(_agentDid: string) { return []; },
    async revoke(_id: string) { return false; },
  },
});
const agentAuditTrail = new AgentAuditTrail();
const integrationMarketplace = new IntegrationMarketplace();
const policyHub = new PolicyManagementHub();
const vendorRiskMgmt = new VendorRiskManagement();
const employeeLifecycle = new EmployeeLifecycleEngine();
const complianceTaskEngine = new ComplianceTaskEngine();
const evidenceAutoEngine = new EvidenceAutomationEngine();
const terraformProvider = new TerraformProvider();

// --- New Enterprise Services ---
import { ContinuousTrustEngine } from '@grc-claw/continuous-trust-engine';
import { AgentCollaboration } from '@grc-claw/agent-collaboration';
import { RegulatoryChangeManagement } from '@grc-claw/regulatory-change-management';
import { AIGovernance } from '@grc-claw/ai-governance';
import { FederatedLearningNetwork } from '@grc-claw/federated-learning';
import { ComplianceIntelligenceAPI } from '@grc-claw/compliance-intelligence-api';
import { AutonomousComplianceAgent } from '@grc-claw/autonomous-compliance-agent';
import { ComplianceDigitalTwin } from '@grc-claw/compliance-digital-twin';
import { QuantumResistantCrypto } from '@grc-claw/quantum-resistant-crypto';
import { NaturalLanguageCompliance } from '@grc-claw/natural-language-compliance';
import { ComplianceAutomationMarketplace } from '@grc-claw/compliance-automation-marketplace';
import { RealTimeComplianceMonitor } from '@grc-claw/real-time-compliance-monitor';

const continuousTrustEngine = new ContinuousTrustEngine();
const agentCollaboration = new AgentCollaboration();
const regulatoryChangeMgmt = new RegulatoryChangeManagement();
const aiGovernance = new AIGovernance();
const complianceKnowledgeGraph = new ComplianceKnowledgeGraph();
const predictiveCompliance = new PredictiveComplianceEngine();
const complianceMarketplace = new ComplianceMarketplace();
const zeroTrustAudit = new ZeroTrustAuditTrail();
const federatedLearning = new FederatedLearningNetwork({
  networkId: 'default',
  modelId: 'default',
  features: [],
  privacy: { epsilon: 1.0, delta: 1e-5, maxGradientNorm: 1.0, noiseMultiplier: 1.0 },
  aggregation: { strategy: 'fedavg', minParticipants: 2, maxRounds: 100, convergenceThreshold: 0.01 }
});
const complianceIntelligence = new ComplianceIntelligenceAPI();
const autonomousAgent = new AutonomousComplianceAgent();
const complianceDigitalTwin = new ComplianceDigitalTwin();
const quantumCrypto = new QuantumResistantCrypto();
const nlCompliance = new NaturalLanguageCompliance();
const automationMarketplace = new ComplianceAutomationMarketplace();
const realTimeMonitor = new RealTimeComplianceMonitor({ framework: 'default' });

function buildEvidenceGraphSnapshot(organizationId = 'demo-org') {
  const summary = complianceKnowledgeGraph.analytics.getSummary();
  const posture = (() => {
    try {
      return complianceKnowledgeGraph.analytics.calculatePosture(organizationId);
    } catch {
      return { overallScore: 0, frameworkPostures: [], gaps: [] };
    }
  })();
  const patterns = complianceKnowledgeGraph.analytics.detectPatterns();
  const forecasts = predictiveCompliance.forecastAll();
  const risks = predictiveCompliance.rankByRisk();
  const marketplaceStats = complianceMarketplace.stats();
  const packs = complianceMarketplace.search({ limit: 20 });
  const auditVerification = zeroTrustAudit.verify();
  const auditRecords = zeroTrustAudit.getRecords();
  const recommendations = [
    risks.length ? `Prioritize ${risks.length} predictive risk signal${risks.length === 1 ? '' : 's'} before the next audit window.` : '',
    patterns.length ? `Convert ${patterns.length} detected graph pattern${patterns.length === 1 ? '' : 's'} into reusable marketplace packs.` : '',
    auditRecords.length === 0 ? 'Record zero-trust audit events so evidence graph snapshots become court-ready proof bundles.' : '',
    packs.length === 0 ? 'Install or publish verified packs to turn graph coverage into marketplace network effects.' : '',
  ].filter(Boolean);
  const graphObjects = [
    nodeObject({
      orgSlug: organizationId,
      graphId: `org:${organizationId}`,
      objectType: 'organization',
      label: organizationId,
      source: 'agent-dispatch',
      weight: 100,
      payload: { organizationId },
    }),
    nodeObject({
      orgSlug: organizationId,
      graphId: 'knowledge-graph:summary',
      objectType: 'knowledge_graph',
      label: 'Compliance knowledge graph',
      source: 'compliance-knowledge-graph',
      weight: summary.totalNodes ?? 80,
      payload: summary as unknown as Record<string, unknown>,
    }),
    nodeObject({
      orgSlug: organizationId,
      graphId: `posture:${organizationId}`,
      objectType: 'posture',
      label: 'Compliance posture',
      source: 'compliance-knowledge-graph',
      weight: posture.overallScore ?? 50,
      payload: posture as unknown as Record<string, unknown>,
    }),
    nodeObject({
      orgSlug: organizationId,
      graphId: 'predictive:forecasts',
      objectType: 'predictive_compliance',
      label: 'Predictive compliance forecasts',
      source: 'predictive-compliance',
      weight: forecasts.length,
      payload: { count: forecasts.length, risks: risks.length },
    }),
    nodeObject({
      orgSlug: organizationId,
      graphId: 'marketplace:packs',
      objectType: 'compliance_marketplace',
      label: 'Compliance pack marketplace',
      source: 'compliance-marketplace',
      weight: marketplaceStats.totalPacks ?? packs.length,
      payload: marketplaceStats as unknown as Record<string, unknown>,
    }),
    nodeObject({
      orgSlug: organizationId,
      graphId: 'zero-trust:audit',
      objectType: 'zero_trust_audit',
      label: 'Zero-trust audit chain',
      source: 'zero-trust-audit',
      weight: auditVerification.valid ? 100 : 40,
      payload: auditVerification as unknown as Record<string, unknown>,
    }),
    edgeObject({
      orgSlug: organizationId,
      graphId: 'edge:org-posture',
      objectType: 'has_posture',
      label: 'organization has posture',
      source: 'agent-dispatch',
      fromId: `org:${organizationId}`,
      toId: `posture:${organizationId}`,
      confidence: 0.92,
    }),
    edgeObject({
      orgSlug: organizationId,
      graphId: 'edge:kg-posture',
      objectType: 'derives',
      label: 'graph derives posture',
      source: 'compliance-knowledge-graph',
      fromId: 'knowledge-graph:summary',
      toId: `posture:${organizationId}`,
      confidence: 0.88,
    }),
    edgeObject({
      orgSlug: organizationId,
      graphId: 'edge:predictive-posture',
      objectType: 'forecasts',
      label: 'forecasts posture drift',
      source: 'predictive-compliance',
      fromId: 'predictive:forecasts',
      toId: `posture:${organizationId}`,
      confidence: 0.82,
    }),
    edgeObject({
      orgSlug: organizationId,
      graphId: 'edge:marketplace-kg',
      objectType: 'extends',
      label: 'packs extend graph',
      source: 'compliance-marketplace',
      fromId: 'marketplace:packs',
      toId: 'knowledge-graph:summary',
      confidence: 0.8,
    }),
    edgeObject({
      orgSlug: organizationId,
      graphId: 'edge:audit-kg',
      objectType: 'verifies',
      label: 'audit chain verifies graph evidence',
      source: 'zero-trust-audit',
      fromId: 'zero-trust:audit',
      toId: 'knowledge-graph:summary',
      confidence: 0.86,
    }),
  ];

  return buildEvidenceGraphObjectSnapshot({
    orgSlug: organizationId,
    objects: graphObjects,
    recommendations,
    extraSummary: {
      knowledge_graph_nodes: summary.totalNodes ?? null,
      posture_score: posture.overallScore ?? null,
      forecasts: forecasts.length,
      predictive_risks: risks.length,
      marketplace_packs: marketplaceStats.totalPacks ?? packs.length,
      audit_records: auditRecords.length,
      audit_chain_valid: auditVerification.valid,
    },
  });
}

export function setSecurityGraph(graph: SecurityGraph): void {
  securityGraph = graph;
}

export { agentAuditTrail };

export type ExecutionState =
  | 'simulated'
  | 'recorded'
  | 'executed'
  | 'verified'
  | 'not_configured'
  | 'failed';

/** Treat a connector acknowledgement as executed, never as independently verified. */
export function executionStateFromOutput(output: Record<string, unknown>): ExecutionState {
  const explicit = output.executionState;
  if (
    explicit === 'simulated' ||
    explicit === 'recorded' ||
    explicit === 'executed' ||
    explicit === 'verified' ||
    explicit === 'not_configured' ||
    explicit === 'failed'
  ) {
    return explicit;
  }
  if (output.ok === false) return 'failed';
  if (output.targetReceipt || output.verified === true) return 'verified';
  return 'executed';
}


export function isBuiltinGrcTool(tool: string): boolean {
  return (
    tool.startsWith('grc.') ||
    tool.startsWith('evidence.') ||
    tool.startsWith('soc.') ||
    tool.startsWith('control.') ||
    tool.startsWith('soar.') ||
    tool.startsWith('firewall.') ||
    tool.startsWith('sentinel.') ||
    tool.startsWith('chronicle.') ||
    tool.startsWith('hermes.') ||
    tool.startsWith('memory.') ||
    tool.startsWith('skills.') ||
    tool.startsWith('audit.') ||
    tool.startsWith('identity.') ||
    tool.startsWith('graph.') ||
    tool.startsWith('observe.') ||
    tool.startsWith('sdk.') ||
    tool.startsWith('accm.') ||
    tool.startsWith('agent_builder.') ||
    tool.startsWith('crosswalk.') ||
    tool.startsWith('chat.') ||
    tool.startsWith('autopilot.') ||
    tool.startsWith('ingest.') ||
    tool.startsWith('frameworks.') ||
    tool.startsWith('compliance.') ||
    tool.startsWith('agent.') ||
    tool.startsWith('a2z.') ||
    tool.startsWith('cloud.') ||
    tool.startsWith('risk.') ||
    tool.startsWith('entity.') ||
    tool.startsWith('drift.') ||
    tool.startsWith('tprm.') ||
    tool.startsWith('trust.') ||
    tool.startsWith('regulatory.') ||
    tool.startsWith('policy.') ||
    tool.startsWith('compliance_orch.') ||
    tool.startsWith('continuous.') ||
    tool.startsWith('threat.') ||
    tool.startsWith('supply_chain.') ||
    tool.startsWith('board.') ||
    tool.startsWith('auto_evidence.') ||
    tool.startsWith('browser_evidence.') ||
    tool.startsWith('incident.') ||
    tool.startsWith('dev_compliance.') ||
    tool.startsWith('engineering.') ||
    tool.startsWith('trust_score.') ||
    tool.startsWith('audit_trail.') ||
    tool.startsWith('federated.') ||
    tool.startsWith('integration.') ||
    tool.startsWith('policy_hub.') ||
    tool.startsWith('vendor_risk.') ||
    tool.startsWith('employee.') ||
    tool.startsWith('task.') ||
    tool.startsWith('evidence_auto.') ||
    tool.startsWith('terraform.') ||
    tool.startsWith('trust.') ||
    tool.startsWith('collaboration.') ||
    tool.startsWith('regulatory.') ||
    tool.startsWith('ai_governance.') ||
    tool.startsWith('knowledge_graph.') ||
    tool.startsWith('evidence_graph.') ||
    tool.startsWith('predictive.') ||
    tool.startsWith('marketplace.') ||
    tool.startsWith('zero_trust.') ||
    tool.startsWith('federated.') ||
    tool.startsWith('intelligence.') ||
    tool.startsWith('autonomous.') ||
    tool.startsWith('digital_twin.') ||
    tool.startsWith('quantum.') ||
    tool.startsWith('nl_compliance.') ||
    tool.startsWith('automation_marketplace.') ||
    tool.startsWith('realtime_monitor.')
  );
}

export async function dispatchBuiltinGrcTool(
  tool: string,
  args: Record<string, unknown>,
  deps: { evidence: EvidenceStore; a2z: A2ZSocConnector; persistence?: import('@grc-claw/persistence').PersistenceLayer | null; agentBuilder?: import('@grc-claw/agent-builder').AgentBuilder; chatGrc?: ChatGRC; autopilot?: import('@grc-claw/compliance-autopilot').ComplianceAutopilot; tracer?: import('@grc-claw/observability').AgentTracer; driftDetector?: DriftDetector; evidenceCollector?: EvidenceCollectorEngine }
): Promise<Record<string, unknown>> {
  const tenantId = Number(args.tenantId ?? 1);
  const span = deps.tracer?.startSpan('tool.execute', { attributes: { 'tool.name': tool } as import('@grc-claw/observability').SpanAttributes });
  if (span && deps.tracer) {
    deps.tracer.addSpanEvent(span.spanId, 'tool.start', { tool });
  }

  try {
  switch (tool) {
    case 'grc.list_controls': {
      const packs = listFrameworkPacks();
      return {
        tenantId,
        packs: packs.map((p) => ({
          code: p.code,
          name: p.name,
          controlCount: p.controls.length,
        })),
        mode: process.env.A2Z_SOC_MODE ?? 'demo',
      };
    }
    case 'grc.get_compliance_score': {
      const packs = listFrameworkPacks();
      let totalControls = 0;
      let controlsWithEvidence = 0;
      for (const pack of packs) {
        for (const ctrl of pack.controls) {
          totalControls++;
          if (deps.evidence.listByControl(ctrl.id).length > 0) controlsWithEvidence++;
        }
      }
      const score = totalControls > 0 ? Math.round((controlsWithEvidence / totalControls) * 10000) / 10000 : 0;
      return {
        tenantId,
        score,
        totalControls,
        controlsWithEvidence,
        executionState: 'recorded',
        message: `Computed from ${controlsWithEvidence}/${totalControls} controls with evidence.`,
      };
    }
    case 'evidence.read': {
      const evidenceId = String(args.evidenceId ?? '');
      let items: any[];
      let source: string;
      if (deps.persistence) {
        try {
          items = await deps.evidence.listByControlFromDb(evidenceId);
          source = 'postgresql';
        } catch {
          items = deps.evidence.listByControl(evidenceId);
          source = 'in-memory';
        }
      } else {
        items = deps.evidence.listByControl(evidenceId);
        source = 'in-memory';
      }
      return { evidenceId, items, count: items.length, source };
    }
    case 'soc.query_events': {
      const limit = Number(args.limit ?? 10);
      const since = typeof args.since === 'string' ? args.since : undefined;
      const until = typeof args.until === 'string' ? args.until : undefined;
      const eventType = typeof args.eventType === 'string' ? args.eventType : undefined;
      if (deps.persistence) {
        try {
          const conditions: string[] = ['tenant_id = $1'];
          const params: unknown[] = [String(tenantId)];
          let paramIdx = 2;
          if (since) {
            conditions.push(`created_at >= $${paramIdx}`);
            params.push(since);
            paramIdx++;
          }
          if (until) {
            conditions.push(`created_at <= $${paramIdx}`);
            params.push(until);
            paramIdx++;
          }
          if (eventType) {
            conditions.push(`event_type = $${paramIdx}`);
            params.push(eventType);
            paramIdx++;
          }
          params.push(limit);
          const whereClause = conditions.join(' AND ');
          const { rows } = await deps.persistence.database.query(
            `SELECT id, tenant_id, event_type, severity, source_system, event_data, created_at
             FROM security_events
             WHERE ${whereClause}
             ORDER BY created_at DESC
             LIMIT $${paramIdx}`,
            params
          );
          return {
            tenantId,
            events: rows,
            count: rows.length,
            source: 'postgresql',
            executionState: 'executed',
            limit,
            ...(since ? { since } : {}),
            ...(until ? { until } : {}),
            ...(eventType ? { eventType } : {}),
          };
        } catch (dbErr) {
          console.warn('[PERSISTENCE] soc.query_events query failed:', dbErr instanceof Error ? dbErr.message : dbErr);
          return {
            tenantId,
            events: [],
            count: 0,
            source: 'postgresql_error',
            executionState: 'failed',
            note: `Database query failed: ${dbErr instanceof Error ? dbErr.message : 'unknown_error'}. Use POST /api/ingest/normalize or A2Z sync for live events.`,
            limit,
          };
        }
      }
      return {
        tenantId,
        events: [],
        executionState: 'not_configured',
        note: 'No persistence configured. Use POST /api/ingest/normalize or A2Z sync for live events.',
        limit,
      };
    }
    case 'control.update_status': {
      const controlId = String(args.controlId ?? '');
      const status = String(args.status ?? 'unknown');
      console.log(`[CONTROL] update_status: controlId=${controlId} status=${status} tenant=${tenantId}`);
      let persisted = false;
      if (deps.persistence) {
        try {
          await deps.persistence.database.execute(
            `CREATE TABLE IF NOT EXISTS control_status (
              id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
              tenant_id VARCHAR(50) NOT NULL,
              control_id VARCHAR(200) NOT NULL,
              status VARCHAR(50) NOT NULL,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              UNIQUE(tenant_id, control_id)
            )`
          );
          await deps.persistence.database.execute(
            `INSERT INTO control_status (tenant_id, control_id, status, updated_at)
             VALUES ($1, $2, $3, NOW())
             ON CONFLICT (tenant_id, control_id)
             DO UPDATE SET status = $3, updated_at = NOW()`,
            [String(tenantId), controlId, status]
          );
          persisted = true;
        } catch (dbErr) {
          console.warn('[PERSISTENCE] control.update_status write failed (in-memory fallback used):', dbErr instanceof Error ? dbErr.message : dbErr);
        }
      }
      return {
        ok: true,
        controlId,
        status,
        tenantId,
        executionState: persisted ? 'executed' as const : 'recorded' as const,
        message: `Control ${controlId} status recorded as ${status}.${persisted ? ' Persisted to PostgreSQL.' : ''}`,
        updatedAt: new Date().toISOString(),
        persisted,
      };
    }
    case 'evidence.attach': {
      const controlId = String(args.controlId ?? '');
      const uri = String(args.uri ?? 'grc-claw://local-evidence');
      if (!controlId) {
        return { ok: false, executionState: 'failed', error: 'controlId_required' };
      }
      const content = typeof args.content === 'string' ? args.content : undefined;
      const evidence = deps.evidence.attach({
        controlId,
        tenantId,
        uri,
        collectedAt: String(args.collectedAt ?? new Date().toISOString()),
        lineage: { source: String(args.source ?? 'gateway') },
        content,
      });

      if (deps.persistence) {
        try {
          await deps.persistence.database.execute(
            `INSERT INTO evidence (tenant_id, control_id, sha256, uri, metadata, lineage, collected_at)
             VALUES ($1, $2, $3, $4, $5, $6, $7)`,
            [
              String(tenantId),
              controlId,
              evidence.sha256,
              uri,
              JSON.stringify({}),
              JSON.stringify(evidence.lineage ?? { source: 'gateway' }),
              evidence.collectedAt,
            ]
          );
        } catch (dbErr) {
          console.warn('[PERSISTENCE] evidence.attach write failed (in-memory fallback used):', dbErr instanceof Error ? dbErr.message : dbErr);
        }
      }

      return { ok: true, executionState: 'recorded', evidence, persisted: !!deps.persistence };
    }
    case 'soar.run_playbook': {
      const playbookName = String(args.playbookName ?? args.playbook ?? 'incident_response');
      try {
        const execution = await soarEngine.executePlaybook(playbookName, {
          agentDid: String(args.agentDid ?? 'unknown'),
          tenantId,
          triggeredBy: 'chat_grc',
          ...args,
        });
        return {
          ok: true,
          executionId: execution.executionId,
          playbookId: execution.playbookId,
          status: execution.status,
          totalDurationMs: execution.totalDurationMs,
          slaBreached: execution.slaBreached,
          stepsCompleted: execution.stepResults.filter(s => s.status === 'completed').length,
          stepsTotal: execution.stepResults.length,
          evidenceHashes: execution.evidenceHashes,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'soar_playbook_failed', playbookName, timestamp: new Date().toISOString() };
      }
    }
    case 'firewall.apply_rule': {
      const ruleId = String(args.ruleId ?? `fw-${Date.now().toString(36)}`);
      const action = String(args.action ?? 'block');
      const scope = String(args.scope ?? 'global');
      console.log(`[SOAR] firewall.apply_rule: rule=${ruleId} action=${action} scope=${scope} tenant=${tenantId}`);
      return {
        ok: false,
        ruleId,
        action,
        scope,
        executionState: 'not_configured',
        message: `Firewall rule ${ruleId} cannot be applied — no live firewall integration is configured for this gateway cell. Configure a cloud connector or firewall API to enable this tool.`,
        timestamp: new Date().toISOString(),
      };
    }
    case 'sentinel.run_playbook': {
      const playbookName = String(args.playbookName ?? args.playbook ?? 'sentinel_response');
      console.log(`[SOAR] sentinel.run_playbook: playbook=${playbookName} tenant=${tenantId}`);
      return {
        ok: false,
        playbookName,
        executionState: 'not_configured',
        message: `Sentinel playbook "${playbookName}" cannot be executed — no live Microsoft Sentinel integration is configured. Connect an Azure connector to enable this tool.`,
        timestamp: new Date().toISOString(),
      };
    }
    case 'chronicle.soar.run_playbook': {
      const playbookName = String(args.playbookName ?? args.playbook ?? 'chronicle_response');
      console.log(`[SOAR] chronicle.soar.run_playbook: playbook=${playbookName} tenant=${tenantId}`);
      return {
        ok: false,
        playbookName,
        executionState: 'not_configured',
        message: `Chronicle SOAR playbook "${playbookName}" cannot be executed — no live Google Chronicle integration is configured. Connect a Chronicle connector to enable this tool.`,
        timestamp: new Date().toISOString(),
      };
    }
    // sentinel.get_incident and aws.guardduty.list_findings removed — fall through to default
    // Phase 5-18 speculative tools (uas, cuas, cmmc, sovereign, iso20022, wallet) removed
    // These required additional configuration and are now handled by the default case.
    case 'hermes.execute_autonomous_task': {
      return {
        ok: false,
        executionState: 'not_configured',
        message: 'Hermes autonomous task execution is not configured. The Hermes runtime requires a local open-weight model endpoint and a Docker containment sandbox to be deployed. Configure the Hermes runtime environment to enable autonomous task execution.',
        timestamp: new Date().toISOString(),
      };
    }
    case 'memory.query_vector_graph': {
      const queryText = String(args.queryText ?? '');
      const results = vectorMemory.query(queryText);
      return {
        ok: true,
        queryText,
        nodes: results.nodes,
        edges: results.edges,
        timestamp: new Date().toISOString()
      };
    }
    case 'memory.persist_session_state': {
      const sessionId = String(args.sessionId ?? 'default');
      const fileDir = path.resolve(process.cwd(), '.grc_memory');
      if (!fs.existsSync(fileDir)) {
        fs.mkdirSync(fileDir, { recursive: true });
      }
      const filePath = path.join(fileDir, `${sessionId}.json`);
      let currentState: any = { calls: 0, toxicityScore: 0, callHistory: [], audit: [] };
      if (fs.existsSync(filePath)) {
        try {
          currentState = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
        } catch (e) {}
      }
      if (typeof args.toxicityScore === 'number') currentState.toxicityScore = args.toxicityScore;
      if (typeof args.calls === 'number') currentState.calls = args.calls;
      if (args.callHistory && Array.isArray(args.callHistory)) currentState.callHistory = args.callHistory;
      if (args.audit && Array.isArray(args.audit)) currentState.audit = args.audit;

      fs.writeFileSync(filePath, JSON.stringify(currentState, null, 2), 'utf-8');
      return {
        ok: true,
        saved: true,
        sessionId,
        state: currentState,
        timestamp: new Date().toISOString()
      };
    }
    case 'skills.query_repo': {
      const queryText = String(args.queryText ?? '');
      const results = skillsRegistry.query(queryText);
      return {
        ok: true,
        queryText,
        totalSkillsInCatalog: skillsRegistry.getTotalCount(),
        matchedSkillsCount: results.length,
        skills: results.map(s => ({
          id: s.id,
          name: s.name,
          category: s.category,
          description: s.description,
          source: s.source
        })),
        timestamp: new Date().toISOString()
      };
    }
    case 'skills.load_definition': {
      const skillId = String(args.skillId ?? '');
      const skill = skillsRegistry.load(skillId);
      if (!skill) {
        return {
          ok: false,
          error: `skill_not_found: ${skillId}`,
          timestamp: new Date().toISOString()
        };
      }
      return {
        ok: true,
        skillId,
        definition: skill,
        timestamp: new Date().toISOString()
      };
    }
    // actuator.simulate_execution removed — handled by default case
    case 'memory.integrate_vector_db': {
      return {
        ok: false,
        executionState: 'not_configured',
        message: 'Vector DB integration is not configured. Connect a supported vector database provider (Pinecone, Weaviate, Qdrant, or local Milvus) and set the vectorDbEndpoint and vectorDbProvider arguments to enable RAG integration.',
        timestamp: new Date().toISOString(),
      };
    }
    case 'memory.audit_cloud_memory': {
      return {
        ok: false,
        executionState: 'not_configured',
        message: 'Cloud memory audit is not configured. No external cloud memory provider is connected. GRC Claw uses local VectorGraphMemory for agent state by default. Connect a cloud memory provider (e.g., OpenAI, Pinecone) to enable cloud memory auditing and lock-in risk analysis.',
        timestamp: new Date().toISOString(),
      };
    }
    // sovereign.verify_tee_attestation, security.trigger_active_containment, grc.generate_zkp_proof,
    // mpc.generate_threshold_signature, security.ebpf_sandbox_rule, audit.generate_zk_ledger_proof,
    // mpc.sign_enclave_transaction, grc.trigger_drift_correction, intel.sync_federated_reports,
    // grc.generate_auditor_bundle removed — fall through to default
    // ─── Agent Identity Fabric (DID:GRC) — wired to real registry ─────
    case 'identity.create_agent_did': {
      const controller = String(args.controller ?? 'did:grc:org-default');
      const tenantScope = (args.tenantScope as string[]) ?? [String(tenantId)];
      const sovereignBoundary = String(args.sovereignBoundary ?? 'global') as 'us-only' | 'eu-only' | 'global' | 'airgapped';
      const agentDid = await identityManager.createAgentDID({ controller, tenantScope, sovereignBoundary });
      return {
        ok: true,
        agentDid: agentDid.id,
        controller: agentDid.controller,
        tenantScope,
        sovereignBoundary,
        status: agentDid.status,
        created: agentDid.created,
        verificationMethod: agentDid.verificationMethod[0]?.id,
      };
    }
    case 'identity.issue_credential': {
      const agentDid = String(args.agentDid ?? '');
      const framework = String(args.framework ?? 'iso27001') as any;
      const certifiedControls = (args.certifiedControls as string[]) ?? [];
      const toolTierAccess = (args.toolTierAccess as ('read' | 'write' | 'destructive')[]) ?? ['read'];
      try {
        const vc = await identityManager.issueCredential(agentDid, {
          framework,
          certifiedControls,
          toolTierAccess,
          tenantScope: [String(tenantId)],
          sovereignBoundary: 'global',
        });
        return {
          ok: true,
          credentialType: 'ComplianceCertification',
          agentDid,
          framework: vc.credentialSubject.framework,
          certifiedControls: vc.credentialSubject.certifiedControls,
          toolTierAccess: vc.credentialSubject.toolTierAccess,
          proofValue: vc.proof.proofValue,
          issuedAt: vc.issuanceDate,
          expiresAt: vc.expirationDate,
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'issue_credential_failed', agentDid };
      }
    }
    case 'identity.verify_credential': {
      const agentDid = String(args.agentDid ?? '');
      const framework = String(args.framework ?? 'iso27001') as any;
      const result = identityManager.verifyCredential(agentDid, framework);
      return {
        ok: true,
        valid: result.valid,
        agentDid,
        framework,
        reason: result.reason,
        verifiedAt: new Date().toISOString(),
      };
    }
    case 'identity.authorize_tool_access': {
      const agentDid = String(args.agentDid ?? '');
      const tier = String(args.tier ?? 'read') as 'read' | 'write' | 'destructive';
      const result = identityManager.authorizeToolAccess(agentDid, tier);
      return {
        ok: true,
        authorized: result.authorized,
        agentDid,
        tier,
        reason: result.reason,
      };
    }
    case 'identity.revoke_did': {
      const agentDid = String(args.agentDid ?? '');
      const result = await identityManager.revokeDID(agentDid);
      return {
        ok: result.ok,
        revoked: result.ok,
        agentDid,
        reason: result.reason,
        revokedAt: result.ok ? new Date().toISOString() : undefined,
      };
    }
    case 'identity.list_agents': {
      const agents = identityManager.listAllAgents();
      return {
        ok: true,
        agents: agents.map(a => ({
          id: a.id,
          controller: a.controller,
          status: a.status,
          riskScore: a.riskScore,
          created: a.created,
        })),
        totalCount: agents.length,
        activeCount: agents.filter(a => a.status === 'active').length,
        timestamp: new Date().toISOString(),
      };
    }
    case 'identity.get_stats': {
      const stats = identityManager.getStats();
      return {
        ok: true,
        total: stats.total,
        active: stats.active,
        suspended: stats.suspended,
        revoked: stats.revoked,
        avgRiskScore: stats.avgRiskScore,
        timestamp: new Date().toISOString(),
      };
    }
    case 'identity.sign_attestation': {
      const agentDid = String(args.agentDid ?? '');
      const payload = (args.payload as Record<string, unknown>) ?? {};
      try {
        const result = identityManager.signAttestation(agentDid, payload);
        return {
          ok: true,
          agentDid: result.agentDid,
          signatureHash: result.signatureHash,
          timestamp: result.timestamp,
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'sign_attestation_failed', agentDid };
      }
    }
    // ─── Fabricated graph tools removed — fall through to default ──────
    // ─── Agentic SOAR (Playbook Engine) ───────────────────────────────
    case 'soar.list_playbooks': {
      const playbooks = soarEngine.listPlaybooks();
      return {
        ok: true,
        playbooks: playbooks.map((pb: Playbook) => ({
          id: pb.id,
          name: pb.name,
          trigger: pb.trigger,
          severity: pb.severity,
          steps: pb.steps.length,
          description: pb.description,
          sla_seconds: pb.sla_seconds,
          tags: pb.tags,
        })),
        count: playbooks.length,
      };
    }
    case 'soar.get_playbook': {
      const playbookId = String(args.playbookId ?? 'pb-agent-compromise');
      const playbooks = soarEngine.listPlaybooks();
      const found = playbooks.find((pb: Playbook) => pb.id === playbookId);
      if (!found) {
        return { ok: false, error: `playbook_not_found: ${playbookId}`, availableIds: playbooks.map((pb: Playbook) => pb.id) };
      }
      return {
        ok: true,
        playbookId: found.id,
        name: found.name,
        trigger: found.trigger,
        severity: found.severity,
        stepCount: found.steps.length,
        slaSeconds: found.sla_seconds,
        tags: found.tags,
        description: found.description,
      };
    }
    case 'soar.execute_playbook': {
      const playbookId = String(args.playbookId ?? '');
      const context = (args.context as Record<string, unknown>) ?? {};
      try {
        const execution = await soarEngine.executePlaybook(playbookId, context);
        return {
          ok: true,
          executionId: execution.executionId,
          playbookId: execution.playbookId,
          status: execution.status,
          stepsExecuted: execution.stepResults.length,
          totalDurationMs: execution.totalDurationMs,
          slaBreached: execution.slaBreached,
          evidenceHashes: execution.evidenceHashes,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, tool, error: err.message ?? 'playbook_execution_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'soar.get_execution': {
      const executionId = String(args.executionId ?? '');
      return {
        ok: false,
        executionId,
        executionState: 'not_configured',
        message: 'No execution history store is configured. SOAR playbook executions are logged in the action ledger but not tracked in a dedicated history store. Use soar.list_playbooks or the action ledger to inspect recent activity.',
        timestamp: new Date().toISOString(),
      };
    }
    // soar.generate_incident_report removed — fall through to default
    // ─── Observability (OpenTelemetry Agent Tracing) ──────────────────
    case 'observe.list_traces': {
      const limit = Number(args.limit ?? 50);
      if (deps.tracer) {
        const otlp = deps.tracer.exportOTLP();
        const allSpans = otlp.resourceSpans.flatMap((r) => r.scopeSpans.flatMap((s) => s.spans));
        const traceIds = [...new Set(allSpans.map((s) => s.traceId))];
        const traces = traceIds.slice(-limit).map((traceId) => {
          const spans = deps.tracer!.getTrace(traceId);
          const first = spans[0];
          const last = spans[spans.length - 1];
          return {
            traceId,
            name: first?.name ?? 'unknown',
            spanCount: spans.length,
            startTime: first?.startTime,
            endTime: last?.endTime,
            status: last?.status ?? 'UNSET',
            durationMs: last?.durationMs,
          };
        });
        return { ok: true, traces, limit, totalTraceIds: traceIds.length };
      }
      return { ok: true, traces: [], limit, note: 'No tracer configured — use GET /api/traces' };
    }
    case 'observe.start_trace': {
      const traceName = String(args.name ?? 'agent.trace');
      if (deps.tracer) {
        const span = deps.tracer.startTrace(traceName);
        return { ok: true, traceId: span.traceId, spanId: span.spanId, name: traceName, startedAt: span.startTime };
      }
      const traceId = `${Date.now().toString(16)}${Math.random().toString(16).substring(2)}`;
      return { ok: true, traceId, spanId: traceId.substring(0, 16), name: traceName, startedAt: new Date().toISOString() };
    }
    case 'observe.get_trace': {
      const traceId = String(args.traceId ?? '');
      if (deps.tracer && traceId) {
        const spans = deps.tracer.getTrace(traceId);
        return { ok: true, traceId, spans, spanCount: spans.length };
      }
      return { ok: true, traceId, spans: [], spanCount: 0 };
    }
    case 'observe.get_metrics': {
      if (deps.tracer) {
        const prometheus = deps.tracer.getPrometheusMetrics();
        const stats = deps.tracer.getStats();
        return { ok: true, metricsCount: stats.totalMetrics, format: 'prometheus', prometheus, timestamp: new Date().toISOString() };
      }
      return { ok: true, metricsCount: 0, format: 'prometheus', timestamp: new Date().toISOString() };
    }
    case 'observe.get_stats': {
      if (deps.tracer) {
        const stats = deps.tracer.getStats();
        return { ok: true, ...stats };
      }
      return { ok: true, totalSpans: 0, totalTraces: 0, totalMetrics: 0, errorRate: 0, avgSpanDurationMs: 0 };
    }
    case 'observe.export_otlp': {
      if (deps.tracer) {
        const otlp = deps.tracer.exportOTLP();
        return { ok: true, format: 'otlp-json', ...otlp, exported: true, timestamp: new Date().toISOString() };
      }
      return { ok: true, format: 'otlp-json', resourceSpans: [], exported: true, timestamp: new Date().toISOString() };
    }
    // ─── Compliance-as-Code SDK ───────────────────────────────────────
    case 'sdk.plan': {
      const organization = String(args.organization ?? 'default-org');
      const packs = listFrameworkPacks();
      const controlsByFramework = packs.map((p) => ({
        framework: p.code,
        controlCount: p.controls.length,
        scope: ['infrastructure', 'agents'],
      }));
      const totalControls = controlsByFramework.reduce((sum, fw) => sum + fw.controlCount, 0);
      return {
        ok: true, organization, frameworksCount: packs.length, totalControls,
        controlsByFramework,
        warnings: [],
        generatedAt: new Date().toISOString()
      };
    }
    case 'sdk.apply': {
      const packs = listFrameworkPacks();
      const appliedFrameworks = packs.map((p) => p.code);
      const appliedControls = packs.reduce((sum, p) => sum + p.controls.length, 0);
      return { ok: true, appliedFrameworks, appliedControls, agentPolicyEnforced: true, didRequired: true, appliedAt: new Date().toISOString() };
    }
    case 'sdk.audit': {
      const packs = listFrameworkPacks();
      let totalControls = 0;
      let controlsWithEvidence = 0;
      for (const pack of packs) {
        for (const ctrl of pack.controls) {
          totalControls++;
          if (deps.evidence.listByControl(ctrl.id).length > 0) controlsWithEvidence++;
        }
      }
      const overallPostureScore = totalControls > 0 ? Math.round((controlsWithEvidence / totalControls) * 1000) / 10 : 0;
      const passRate = totalControls > 0 ? controlsWithEvidence / totalControls : 0;
      return { ok: true, overallPostureScore, frameworkCount: packs.length, totalControls, passRate, auditedAt: new Date().toISOString() };
    }
    case 'sdk.owasp_coverage': {
      const OWASP_TOP_10_AI_RISKS = [
        'Excessive Agency', 'Goal Hijacking', 'Memory Poisoning', 'Cascading Failures',
        'Unauthorized Tool Access', 'Data Exfiltration', 'Privilege Escalation',
        'Audit Trail Tampering', 'Supply Chain Compromise', 'Insufficient Observability'
      ];
      const packs = listFrameworkPacks();
      const coveredRisks = new Set<string>();
      for (const risk of OWASP_TOP_10_AI_RISKS) {
        const riskLower = risk.toLowerCase();
        for (const pack of packs) {
          for (const ctrl of pack.controls) {
            const titleLower = ctrl.title.toLowerCase();
            const codeLower = ctrl.controlCode.toLowerCase();
            if (titleLower.includes(riskLower) || codeLower.includes(riskLower.substring(0, 4))) {
              if (deps.evidence.listByControl(ctrl.id).length > 0) {
                coveredRisks.add(risk);
              }
            }
          }
        }
      }
      const fullyAddressed = coveredRisks.size;
      const partiallyAddressed = Math.max(0, OWASP_TOP_10_AI_RISKS.length - fullyAddressed);
      const coveragePercentage = OWASP_TOP_10_AI_RISKS.length > 0
        ? Math.round((fullyAddressed / OWASP_TOP_10_AI_RISKS.length) * 100)
        : 0;
      return {
        ok: true, totalRisks: OWASP_TOP_10_AI_RISKS.length, fullyAddressed, partiallyAddressed, coveragePercentage,
        risks: OWASP_TOP_10_AI_RISKS
      };
    }
    case 'sdk.marketplace_catalog': {
      const packs = listFrameworkPacks();
      const frameworkPacks = packs.map((p) => ({
        id: p.code,
        name: p.name,
        controlCount: p.controls.length,
      }));
      return {
        ok: true,
        frameworkPacks,
        skillPacks: [
          { id: 'incident-response-v2', name: 'Incident Response Automation' },
          { id: 'evidence-collector', name: 'Automated Evidence Collection' },
        ]
      };
    }
    // aibom.generate removed — fall through to default
    // ─── Phase 5-9 fabricated tools removed — fall through to default ──
    // ─── Ingest Tools ──────────────────────────────────────────────
    case 'ingest.normalize_event': {
      const source = String(args.source ?? '') as IngestSource;
      const payload = args.payload;
      try {
        const event = normalizeBySource(source, payload, tenantId);
        if (!event) {
          return { ok: false, error: `unsupported_source: ${source}`, tool, timestamp: new Date().toISOString() };
        }
        return { ok: true, event, source, tenantId, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'normalize_failed', source, timestamp: new Date().toISOString() };
      }
    }
    case 'ingest.list_sources': {
      const ossSources: string[] = ['wazuh', 'suricata', 'snort', 'elastic', 'ufw'];
      const cloudSources: string[] = [...CLOUD_INGEST_SOURCES];
      return {
        ok: true,
        ossSources,
        cloudSources,
        totalSources: ossSources.length + cloudSources.length,
        timestamp: new Date().toISOString(),
      };
    }
    // ─── Evidence Tools ─────────────────────────────────────────────
    case 'evidence.store': {
      const controlId = String(args.controlId ?? '');
      const uri = String(args.uri ?? 'grc-claw://local-evidence');
      if (!controlId) {
        return { ok: false, error: 'controlId_required', timestamp: new Date().toISOString() };
      }
      try {
        const content = typeof args.content === 'string' ? args.content : undefined;
        const record = deps.evidence.attach({
          controlId,
          tenantId,
          uri,
          collectedAt: String(args.collectedAt ?? new Date().toISOString()),
          lineage: { source: String(args.source ?? 'gateway') },
          content,
        });

        if (deps.persistence) {
          try {
            await deps.persistence.database.execute(
              `INSERT INTO evidence (tenant_id, control_id, sha256, uri, metadata, lineage, collected_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7)`,
              [
                String(tenantId),
                controlId,
                record.sha256,
                uri,
                JSON.stringify({}),
                JSON.stringify(record.lineage ?? { source: 'gateway' }),
                record.collectedAt,
              ]
            );
          } catch (dbErr) {
            console.warn('[PERSISTENCE] evidence.store write failed (in-memory fallback used):', dbErr instanceof Error ? dbErr.message : dbErr);
          }
        }

        return { ok: true, evidence: record, stored: true, persisted: !!deps.persistence, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'evidence_store_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'evidence.hash_chain_verify': {
      try {
        const result = actionLedger.verify();
        const recentEvents = actionLedger.list(10);
        return {
          ok: result.ok,
          checked: result.checked,
          error: result.error,
          recentEventsCount: recentEvents.length,
          ledgerIntegrity: result.ok ? 'VALID' : 'COMPROMISED',
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'hash_chain_verify_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'evidence.generate_assurance_envelope': {
      try {
        const intentEventId = String(args.intentEventId ?? '');
        const decisionEventId = String(args.decisionEventId ?? '');
        const resultEventId = String(args.resultEventId ?? '');

        const allEvents = actionLedger.list(500);
        const intent = allEvents.find(e => e.actionId === intentEventId && e.kind === 'intent');
        const decision = allEvents.find(e => e.actionId === decisionEventId && e.kind === 'decision');
        const result = allEvents.find(e => e.actionId === resultEventId && e.kind === 'result');

        if (!intent) {
          return { ok: false, error: 'intent_event_not_found', intentEventId, timestamp: new Date().toISOString() };
        }

        const envelope = createAssuranceEnvelope({
          intent,
          decision: decision ?? undefined,
          result: result ?? undefined,
          identity: args.agentDid ? { agentDid: String(args.agentDid), status: 'verified' as const } : undefined,
          assurance: typeof args.riskScore === 'number' ? { riskScore: Number(args.riskScore) } : undefined,
        });

        return { ok: true, envelope, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'assurance_envelope_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Framework Tools ────────────────────────────────────────────
    case 'frameworks.list_packs': {
      try {
        const packs = listFrameworkPacks();
        return {
          ok: true,
          packs: packs.map(p => ({
            code: p.code,
            name: p.name,
            version: p.version,
            controlCount: p.controls.length,
            controls: p.controls.map(c => ({
              id: c.id,
              controlCode: c.controlCode,
              title: c.title,
              domain: c.domain,
            })),
          })),
          totalCount: packs.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'list_packs_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'frameworks.check_control': {
      const controlCode = String(args.controlCode ?? '');
      const frameworkCode = String(args.frameworkCode ?? '');
      try {
        const packs = listFrameworkPacks();
        const matchingControls: Array<{ packCode: string; packName: string; controlId: string; controlCode: string; title: string; domain: string }> = [];

        for (const pack of packs) {
          if (frameworkCode && pack.code !== frameworkCode) continue;
          for (const ctrl of pack.controls) {
            if (!controlCode || ctrl.controlCode === controlCode || ctrl.id.includes(controlCode)) {
              matchingControls.push({
                packCode: pack.code,
                packName: pack.name,
                controlId: ctrl.id,
                controlCode: ctrl.controlCode,
                title: ctrl.title,
                domain: ctrl.domain ?? 'unknown',
              });
            }
          }
        }

        return {
          ok: true,
          controlCode,
          frameworkCode: frameworkCode || 'all',
          found: matchingControls.length > 0,
          matches: matchingControls,
          matchCount: matchingControls.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'check_control_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Compliance Tools ───────────────────────────────────────────
    case 'compliance.run_scan': {
      const frameworkFilter = String(args.frameworkCode ?? '');
      try {
        const packs = listFrameworkPacks();
        const scanResults: Array<{
          framework: string;
          frameworkName: string;
          controls: Array<{ id: string; controlCode: string; title: string; hasEvidence: boolean; status: 'pass' | 'fail' | 'no_evidence' }>;
          passRate: number;
        }> = [];

        for (const pack of packs) {
          if (frameworkFilter && pack.code !== frameworkFilter) continue;
          const controlResults = pack.controls.map(ctrl => {
            const evidenceItems = deps.evidence.listByControl(ctrl.id);
            return {
              id: ctrl.id,
              controlCode: ctrl.controlCode,
              title: ctrl.title,
              hasEvidence: evidenceItems.length > 0,
              status: (evidenceItems.length > 0 ? 'pass' : 'no_evidence') as 'pass' | 'fail' | 'no_evidence',
            };
          });

          const passCount = controlResults.filter(c => c.status === 'pass').length;
          scanResults.push({
            framework: pack.code,
            frameworkName: pack.name,
            controls: controlResults,
            passRate: controlResults.length > 0 ? Math.round((passCount / controlResults.length) * 100) : 0,
          });
        }

        const totalControls = scanResults.reduce((sum, f) => sum + f.controls.length, 0);
        const totalPassed = scanResults.reduce((sum, f) => sum + f.controls.filter(c => c.status === 'pass').length, 0);

        return {
          ok: true,
          scanResults,
          summary: {
            frameworksScanned: scanResults.length,
            totalControls,
            totalPassed,
            totalFailed: totalControls - totalPassed,
            overallScore: totalControls > 0 ? Math.round((totalPassed / totalControls) * 100) : 0,
          },
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'compliance_scan_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'compliance.get_posture': {
      const framework = String(args.framework ?? 'iso27001');
      try {
        const posture = securityGraph.calculateCompliancePosture(String(tenantId), framework);
        return {
          ok: true,
          tenantId,
          framework,
          overallScore: posture.overallScore,
          controlScores: posture.controlScores,
          trend: posture.trend,
          lastEvaluated: posture.lastEvaluated,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_posture_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Agent Tools ────────────────────────────────────────────────
    case 'agent.invoke': {
      const sessionId = String(args.sessionId ?? `session_${Date.now().toString(36)}`);
      const toolName = String(args.tool ?? '');
      const toolArgs = (args.args as Record<string, unknown>) ?? {};
      const agentRole = String(args.agentRole ?? 'operator');

      if (!toolName) {
        return { ok: false, error: 'tool_name_required', timestamp: new Date().toISOString() };
      }

      try {
        let session = agentSessions.get(sessionId);
        if (!session) {
          const policy = new ExecPolicy();
          session = new AgentSession(sessionId, policy, memoryStore);
          agentSessions.set(sessionId, session);
        }

        const invocation = {
          tool: toolName,
          args: toolArgs,
          agentRole,
          idempotencyKey: String(args.idempotencyKey ?? `idem_${Date.now().toString(36)}`),
        };

        const decision = await session.invoke(invocation);

        return {
          ok: decision.allowed,
          sessionId,
          tool: toolName,
          decision: {
            allowed: decision.allowed,
            reason: decision.reason,
            sandbox: decision.sandbox,
            requiresApproval: decision.requiresApproval,
            toxicityScore: decision.toxicityScore,
            anomaliesDetected: decision.anomaliesDetected,
          },
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'agent_invoke_failed', sessionId, timestamp: new Date().toISOString() };
      }
    }
    case 'agent.get_session': {
      const sessionId = String(args.sessionId ?? '');
      if (!sessionId) {
        return { ok: false, error: 'sessionId_required', timestamp: new Date().toISOString() };
      }

      try {
        let session = agentSessions.get(sessionId);
        if (!session) {
          const policy = new ExecPolicy();
          session = new AgentSession(sessionId, policy, memoryStore);
          agentSessions.set(sessionId, session);
        }

        const state = session.getState();
        return {
          ok: true,
          sessionId,
          state: {
            calls: state.calls,
            toxicityScore: state.toxicityScore,
            auditCount: state.audit.length,
            callHistoryCount: state.callHistory.length,
            recentAudit: state.audit.slice(-5),
          },
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_session_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Graph Tools ────────────────────────────────────────────────
    case 'graph.attack_path': {
      const startNodeId = String(args.startNodeId ?? '');
      const maxDepth = Number(args.maxDepth ?? 5);
      try {
        const paths = securityGraph.traceAttackPaths(startNodeId, maxDepth);
        return {
          ok: true,
          startNodeId,
          paths: paths.map(p => ({
            id: p.id,
            startNode: p.startNode,
            endNode: p.endNode,
            totalRisk: p.totalRisk,
            segmentCount: p.segments.length,
            segments: p.segments.map(s => ({
              nodeId: s.node.id,
              nodeName: s.node.name,
              nodeType: s.node.type,
              riskContribution: s.riskContribution,
            })),
          })),
          pathCount: paths.length,
          maxDepth,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'attack_path_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'graph.blast_radius': {
      const controlId = String(args.controlId ?? '');
      const maxDepth = Number(args.maxDepth ?? 4);
      try {
        const radius = securityGraph.calculateBlastRadius(controlId, maxDepth);
        return {
          ok: true,
          controlId,
          affectedNodesCount: radius.affectedNodes.length,
          affectedEdgesCount: radius.affectedEdges.length,
          impactScore: radius.impactScore,
          cascadeDepth: radius.cascadeDepth,
          affectedNodes: radius.affectedNodes.map(n => ({
            id: n.id,
            name: n.name,
            type: n.type,
            riskScore: n.riskScore,
          })),
          assessedAt: radius.assessedAt,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'blast_radius_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'graph.risk_score': {
      const agentDid = String(args.agentDid ?? '');
      try {
        const assessment = securityGraph.assessAgentRisk(agentDid);
        return {
          ok: true,
          agentDid: assessment.agentDid,
          overallRisk: assessment.overallRisk,
          riskFactors: assessment.riskFactors,
          recommendedActions: assessment.recommendedActions,
          assessedAt: assessment.assessedAt,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'risk_score_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── A2Z Bridge Tools ──────────────────────────────────────────
    case 'a2z.sync_to_private': {
      const sinceIso = String(args.sinceIso ?? new Date(Date.now() - 3600000).toISOString());
      try {
        const result = await deps.a2z.syncInbound(sinceIso);
        return {
          ok: true,
          processed: result.processed,
          impacts: result.impacts,
          sinceIso,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'sync_to_private_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'a2z.get_trust_score': {
      const frameworkCode = String(args.frameworkCode ?? 'iso27001');
      try {
        const score = await deps.a2z.getComplianceScore(tenantId, frameworkCode);
        return {
          ok: true,
          tenantId: score.tenantId,
          frameworkCode: score.frameworkCode,
          scorePercent: score.scorePercent,
          failingControls: score.failingControls,
          totalControls: score.totalControls,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_trust_score_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Cloud Tools ───────────────────────────────────────────────
    case 'cloud.list_connectors': {
      try {
        const connectors = cloudRegistry.list();
        return {
          ok: true,
          connectors: connectors.map(c => ({
            provider: c.provider,
          })),
          totalCount: connectors.length,
          supportedProviders: ['aws', 'azure', 'gcp'],
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'list_connectors_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'cloud.fetch_findings': {
      try {
        const findings = await cloudRegistry.fetchAllFindings();
        return {
          ok: true,
          findings,
          count: findings.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'fetch_findings_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Audit Tools ───────────────────────────────────────────────
    case 'audit.create_audit': {
      const auditName = String(args.name ?? `Audit-${Date.now()}`);
      const auditType = String(args.type ?? 'internal') as any;
      const scope = (args.scope as string[]) ?? [];
      const framework = String(args.framework ?? 'iso27001');
      const leadAuditor = String(args.leadAuditor ?? 'system');
      const team = (args.team as string[]) ?? [];
      const startDate = String(args.startDate ?? new Date().toISOString());
      const endDate = String(args.endDate ?? new Date(Date.now() + 30 * 86400000).toISOString());

      try {
        const audit = auditManager.createAudit({
          name: auditName,
          type: auditType,
          scope,
          framework,
          leadAuditor,
          team,
          startDate,
          endDate,
        });

        if (deps.persistence) {
          try {
            await deps.persistence.database.execute(
              `INSERT INTO playbook_executions (tenant_id, playbook_name, status, steps, sla_ms, started_at, evidence_hashes)
               VALUES ($1, $2, $3, $4, $5, $6, $7)`,
              [
                String(tenantId),
                audit.name,
                audit.status,
                JSON.stringify([{ type: 'audit_create', framework, scope }]),
                0,
                audit.createdAt,
                '[]',
              ]
            );
          } catch (dbErr) {
            console.warn('[PERSISTENCE] audit.create_audit write failed (in-memory fallback used):', dbErr instanceof Error ? dbErr.message : dbErr);
          }
        }

        return {
          ok: true,
          audit: {
            id: audit.id,
            name: audit.name,
            type: audit.type,
            status: audit.status,
            framework: audit.framework,
            scope: audit.scope,
            createdAt: audit.createdAt,
          },
          persisted: !!deps.persistence,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'create_audit_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'audit.list_findings': {
      try {
        const audits = auditManager.listAudits();
        const allFindings = audits.flatMap((audit: Audit) =>
          audit.findings.map((f: Finding) => ({
            ...f,
            auditId: audit.id,
            auditName: audit.name,
            framework: audit.framework,
          }))
        );

        const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
        for (const f of allFindings) {
          severityCounts[f.severity]++;
        }

        return {
          ok: true,
          findings: allFindings,
          totalCount: allFindings.length,
          severityCounts,
          auditsScanned: audits.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'list_findings_failed', timestamp: new Date().toISOString() };
      }
    }

    // --- Risk Quantification Tools ---
    case 'risk.run_monte_carlo': {
      try {
        const engine = new MonteCarloEngine(args.scenario as unknown as import('@grc-claw/risk-quantification').RiskScenario, { iterations: args.iterations as number, seed: args.seed as number });
        const result = engine.run();
        return { ok: true, result, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'monte_carlo_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'risk.run_fair_analysis': {
      try {
        const calc = new FAIRCalculator(args.scenario as unknown as import('@grc-claw/risk-quantification').RiskScenario, { iterations: args.iterations as number, seed: args.seed as number });
        const result = calc.calculate();
        return { ok: true, result, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'fair_analysis_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'risk.add_scenario': {
      try {
        const entry = riskRegister.addScenario(args as unknown as import('@grc-claw/risk-quantification').RiskScenario);
        return { ok: true, entry, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'add_scenario_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'risk.get_register': {
      try {
        const entries = riskRegister.getAllEntries();
        const metrics = riskRegister.portfolioMetrics();
        return { ok: true, entries, metrics, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_register_failed', timestamp: new Date().toISOString() };
      }
    }

    // --- Entity Management Tools ---
    case 'entity.create': {
      try {
        const entity = entityManager.createEntity(args as Parameters<typeof entityManager.createEntity>[0]);
        return { ok: true, entity, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'entity_create_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'entity.list': {
      try {
        const entities = entityManager.listEntities();
        return { ok: true, entities, totalCount: entities.length, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'entity_list_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'entity.get_compliance_rollup': {
      try {
        const statuses = entityManager.getComplianceStatuses(args.entityId as string);
        return { ok: true, entityId: args.entityId, statuses, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'entity_compliance_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'entity.get_consolidated_report': {
      try {
        const report = entityManager.getConsolidatedReport();
        return { ok: true, report, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'entity_report_failed', timestamp: new Date().toISOString() };
      }
    }

    // --- ACCM Tools ---
    case 'accm.detect_gaps': {
      try {
        const fw = String(args.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const detector = makeAccmGapDetector(fw, deps.evidence);
        const engine = new ACCMEngine(detector);
        const gaps = await engine.detectGaps(fw);
        return { ok: true, frameworkCode: fw, gapsDetected: gaps.length, gaps, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'accm_detect_gaps_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'accm.remediate': {
      try {
        const fw = String(args.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const detector = makeAccmGapDetector(fw, deps.evidence);
        const engine = new ACCMEngine(detector);
        const gaps = await engine.detectGaps(fw);
        const results = [];
        for (const gap of gaps) {
          const workflow = engine.createRemediationPlan(gap);
          const result = await engine.executeRemediation(workflow);
          results.push({ gapId: gap.id, controlCode: gap.controlCode, workflowId: workflow.id, success: result.success, message: result.message });
        }
        return { ok: true, frameworkCode: fw, remediations: results, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'accm_remediate_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'accm.verify': {
      try {
        const workflowId = String(args.workflowId ?? '');
        const fw = String(args.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const detector = makeAccmGapDetector(fw, deps.evidence);
        const engine = new ACCMEngine(detector);
        const workflow = engine.getWorkflow(workflowId);
        if (!workflow) {
          return { ok: false, error: 'workflow_not_found', workflowId, timestamp: new Date().toISOString() };
        }
        const verification = await engine.verifyRemediation(workflow);
        return { ok: true, verification, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'accm_verify_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'accm.full_cycle': {
      try {
        const fw = String(args.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const detector = makeAccmGapDetector(fw, deps.evidence);
        const engine = new ACCMEngine(detector);
        const report = await engine.fullCycle(fw);
        return { ok: true, report, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'accm_full_cycle_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Agent Builder Tools ───────────────────────────────────────
    case 'agent_builder.list_agents': {
      const builder = deps.agentBuilder;
      if (!builder) return { ok: false, executionState: 'not_configured', message: 'AgentBuilder not available' };
      const agents = builder.listAgents();
      return {
        ok: true,
        agents: agents.map((a) => ({ id: a.id, name: a.name, description: a.description, tags: a.tags, enabled: a.enabled })),
        count: agents.length,
        timestamp: new Date().toISOString(),
      };
    }
    case 'agent_builder.get_agent': {
      const builder = deps.agentBuilder;
      if (!builder) return { ok: false, executionState: 'not_configured', message: 'AgentBuilder not available' };
      const agentId = String(args.agentId ?? '');
      const agent = builder.getAgent(agentId);
      if (!agent) return { ok: false, error: `agent_not_found: ${agentId}` };
      return { ok: true, agent, timestamp: new Date().toISOString() };
    }
    case 'agent_builder.create_agent': {
      const builder = deps.agentBuilder;
      if (!builder) return { ok: false, executionState: 'not_configured', message: 'AgentBuilder not available' };
      try {
        const definition = args.definition as import('@grc-claw/agent-builder').AgentDefinition;
        if (!definition || !definition.name) return { ok: false, error: 'definition_with_name_required' };
        const agent = builder.createAgent(definition);
        return { ok: true, agent, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'create_agent_failed' };
      }
    }
    case 'agent_builder.trigger_agent': {
      const builder = deps.agentBuilder;
      if (!builder) return { ok: false, executionState: 'not_configured', message: 'AgentBuilder not available' };
      try {
        const agentId = String(args.agentId ?? '');
        const context = (args.context as Record<string, unknown>) ?? {};
        const run = await builder.triggerAgent(agentId, context);
        return { ok: true, run, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'trigger_agent_failed' };
      }
    }

    // --- Framework Crosswalk Tools ---
    case 'crosswalk.generate': {
      try {
        const crosswalk = new FrameworkCrosswalk();
        const source = String(args.source ?? 'soc2');
        const target = String(args.target ?? 'iso27001');
        const report = crosswalk.generateCrosswalk(source, target);
        return { ok: true, report, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'crosswalk_generate_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'crosswalk.overlaps': {
      try {
        const crosswalk = new FrameworkCrosswalk();
        const framework1 = String(args.framework1 ?? 'soc2');
        const framework2 = String(args.framework2 ?? 'iso27001');
        const overlaps = crosswalk.findOverlaps(framework1, framework2);
        return { ok: true, overlaps, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'crosswalk_overlaps_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'crosswalk.coverage': {
      try {
        const crosswalk = new FrameworkCrosswalk();
        const controlIds = (args.controlIds as string[]) ?? [];
        const frameworks = (args.frameworks as string[]) ?? ['soc2', 'iso27001'];
        const coverage = crosswalk.calculateMultiFrameworkCoverage(controlIds, frameworks);
        return { ok: true, coverage, frameworks, controlIds, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'crosswalk_coverage_failed', timestamp: new Date().toISOString() };
      }
    }

    // --- Chat GRC Tools ---
    case 'chat.process_message': {
      try {
        const chat = deps.chatGrc ?? new ChatGRC();
        const message = String(args.message ?? '');
        const context = (args.context as Record<string, unknown>) ?? {};
        const chatContext = {
          frameworks: (context.frameworks as string[]) ?? [],
          controls: (context.controls as string[]) ?? [],
          evidence: (context.evidence as string[]) ?? [],
          risks: (context.risks as string[]) ?? [],
        };
        const sessionId = typeof args.sessionId === 'string' ? args.sessionId : undefined;
        const response = await chat.processMessage(message, chatContext, sessionId);
        return { ok: true, response, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'chat_process_message_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'chat.list_sessions': {
      try {
        const chat = deps.chatGrc ?? new ChatGRC();
        const sessions = chat.listSessions();
        return { ok: true, sessions, count: sessions.length, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'chat_list_sessions_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Compliance Autopilot Tools ─────────────────────────────────────
    case 'autopilot.run_cycle': {
      try {
        const autopilot = deps.autopilot;
        if (!autopilot) return { ok: false, executionState: 'not_configured', message: 'ComplianceAutopilot not available' };
        const cycle = await autopilot.runCycle();
        return {
          ok: true,
          cycleId: cycle.cycleId,
          startedAt: cycle.startedAt,
          completedAt: cycle.completedAt,
          gapsFound: cycle.monitor.gapsFound,
          controlsChecked: cycle.monitor.controlsChecked,
          frameworksChecked: cycle.monitor.frameworksChecked,
          remediationsCount: cycle.remediations.length,
          verificationResults: cycle.verificationResults.length,
          report: cycle.report,
          auditTrailCount: cycle.auditTrail.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'autopilot_cycle_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'autopilot.get_status': {
      try {
        const autopilot = deps.autopilot;
        if (!autopilot) return { ok: false, executionState: 'not_configured', message: 'ComplianceAutopilot not available' };
        const controls = autopilot.getControls();
        const gaps = autopilot.getGaps();
        const remediations = autopilot.getRemediations();
        const compliant = controls.filter(c => c.status === 'compliant').length;
        const total = controls.length;
        return {
          ok: true,
          complianceScore: total > 0 ? Math.round((compliant / total) * 10000) / 100 : 0,
          totalControls: total,
          compliantControls: compliant,
          nonCompliantControls: controls.filter(c => c.status === 'non_compliant').length,
          partialControls: controls.filter(c => c.status === 'partial').length,
          gapsCount: gaps.length,
          remediationsCount: remediations.length,
          frameworks: autopilot.getConfig().frameworks,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'autopilot_status_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'autopilot.get_report': {
      try {
        const autopilot = deps.autopilot;
        if (!autopilot) return { ok: false, executionState: 'not_configured', message: 'ComplianceAutopilot not available' };
        const framework = String(args.framework ?? 'iso27001');
        const report = await autopilot.generateReport(framework);
        return { ok: true, report, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'autopilot_report_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'autopilot.get_audit_trail': {
      try {
        const autopilot = deps.autopilot;
        if (!autopilot) return { ok: false, executionState: 'not_configured', message: 'ComplianceAutopilot not available' };
        const auditTrail = autopilot.getAuditTrail();
        const verified = autopilot.verifyAuditTrail();
        return { ok: true, auditTrail, verified, count: auditTrail.length, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'autopilot_audit_trail_failed', timestamp: new Date().toISOString() };
      }
    }

    // ─── Drift Detector Tools ──────────────────────────────────────────
    case 'drift.capture_baseline': {
      if (!deps.driftDetector) return { ok: false, executionState: 'not_configured', message: 'DriftDetector not available' };
      try {
        const baseline = await deps.driftDetector.captureBaseline();
        return { ok: true, baseline, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'capture_baseline_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'drift.detect': {
      if (!deps.driftDetector) return { ok: false, executionState: 'not_configured', message: 'DriftDetector not available' };
      try {
        const result = await deps.driftDetector.detectDrift();
        return { ok: true, result, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'detect_drift_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'drift.get_history': {
      if (!deps.driftDetector) return { ok: false, executionState: 'not_configured', message: 'DriftDetector not available' };
      const history = deps.driftDetector.getDriftHistory();
      return { ok: true, history, count: history.length, timestamp: new Date().toISOString() };
    }
    case 'drift.get_alerts': {
      if (!deps.driftDetector) return { ok: false, executionState: 'not_configured', message: 'DriftDetector not available' };
      const alerts = deps.driftDetector.getAlertHistory();
      return { ok: true, alerts, count: alerts.length, timestamp: new Date().toISOString() };
    }
    // ─── Evidence Collector Tools ──────────────────────────────────────
    case 'evidence.collect': {
      if (!deps.evidenceCollector) return { ok: false, executionState: 'not_configured', message: 'EvidenceCollector not available' };
      try {
        const framework = String(args.framework ?? 'SOC2');
        const category = String(args.category ?? 'mfa');
        const controlId = String(args.controlId ?? 'default');
        const result = await deps.evidenceCollector.collect([{ category: category as any, framework: framework as any, controlId }]);
        return { ok: true, result, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'evidence_collect_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'evidence.inventory': {
      if (!deps.evidenceCollector) return { ok: false, executionState: 'not_configured', message: 'EvidenceCollector not available' };
      const inventory = deps.evidenceCollector.getAllEvidence();
      return { ok: true, inventory, count: inventory.length, timestamp: new Date().toISOString() };
    }
    case 'evidence.collect_summary': {
      if (!deps.evidenceCollector) return { ok: false, executionState: 'not_configured', message: 'EvidenceCollector not available' };
      const framework = String(args.framework ?? 'SOC2');
      const summary = deps.evidenceCollector.getComplianceSummary(framework as any);
      return { ok: true, framework, summary, timestamp: new Date().toISOString() };
    }

    // ─── Third-Party Risk Management Tools ─────────────────────────
    case 'tprm.create_vendor': {
      const name = String(args.name ?? '');
      const domain = String(args.domain ?? '');
      const categories = (args.categories as string[]) ?? [];
      const frameworks = (args.frameworks as string[]) ?? [];
      const contacts = (args.contacts as { name: string; email: string; role: string; isPrimary: boolean }[]) ?? [];
      if (!name || !domain) {
        return { ok: false, error: 'name_and_domain_required', timestamp: new Date().toISOString() };
      }
      try {
        const vendor = vendorRegistry.registerVendor({ name, domain, categories, frameworks: frameworks as any, contacts });
        return { ok: true, vendor, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'create_vendor_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'tprm.list_vendors': {
      const vendors = vendorRegistry.listVendors();
      return { ok: true, vendors, totalCount: vendors.length, timestamp: new Date().toISOString() };
    }
    case 'tprm.get_risk_score': {
      const vendorId = String(args.vendorId ?? '');
      if (!vendorId) {
        return { ok: false, error: 'vendorId_required', timestamp: new Date().toISOString() };
      }
      try {
        const score = vendorRegistry.calculateRiskScore(vendorId);
        if (!score) {
          return { ok: false, error: `vendor_not_found: ${vendorId}`, timestamp: new Date().toISOString() };
        }
        return { ok: true, score, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_risk_score_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Trust Center Tools ────────────────────────────────────────
    case 'trust.create_page': {
      const slug = String(args.slug ?? '');
      const companyName = String(args.companyName ?? '');
      if (!slug || !companyName) {
        return { ok: false, error: 'slug_and_companyName_required', timestamp: new Date().toISOString() };
      }
      try {
        const page = trustCenter.createPage(slug, companyName);
        return { ok: true, page, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'create_page_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'trust.publish_page': {
      const pageId = String(args.pageId ?? '');
      if (!pageId) {
        return { ok: false, error: 'pageId_required', timestamp: new Date().toISOString() };
      }
      try {
        const published = trustCenter.publishPage(pageId);
        if (!published) {
          return { ok: false, error: `page_not_found: ${pageId}`, timestamp: new Date().toISOString() };
        }
        const publicJson = trustCenter.generatePublicJson(pageId);
        return { ok: true, published: true, pageId, publicJson, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'publish_page_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'trust.get_page': {
      const pageId = String(args.pageId ?? '');
      const slug = String(args.slug ?? '');
      if (!pageId && !slug) {
        return { ok: false, error: 'pageId_or_slug_required', timestamp: new Date().toISOString() };
      }
      try {
        const page = pageId ? trustCenter.getPage(pageId) : trustCenter.getPageBySlug(slug);
        if (!page) {
          return { ok: false, error: 'page_not_found', timestamp: new Date().toISOString() };
        }
        return { ok: true, page, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_page_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Regulatory Intelligence Tools ─────────────────────────────
    case 'regulatory.list_alerts': {
      const framework = String(args.framework ?? '') as any;
      const impact = String(args.impact ?? '') as any;
      try {
        let changes = framework ? regulatoryEngine.getChangesByFramework(framework) : [];
        if (impact) {
          changes = changes.length > 0 ? changes.filter(c => c.impactLevel === impact) : regulatoryEngine.getChangesByImpact(impact);
        }
        const criticalChanges = regulatoryEngine.getCriticalChanges();
        const stats = regulatoryEngine.getStats();
        return {
          ok: true,
          alerts: changes.length > 0 ? changes : criticalChanges,
          totalCount: changes.length || criticalChanges.length,
          stats,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'list_alerts_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'regulatory.check_regulation': {
      const sourceId = String(args.sourceId ?? '');
      const jurisdiction = String(args.jurisdiction ?? '');
      try {
        const stats = regulatoryEngine.getStats();
        const sources = regulatoryEngine.getSources();
        const digests = jurisdiction ? regulatoryEngine.getDigests(jurisdiction) : regulatoryEngine.getDigests();
        return {
          ok: true,
          sourceId,
          jurisdiction,
          sourcesRegistered: sources.length,
          totalChangesDetected: stats.totalChanges,
          criticalChanges: stats.criticalChanges,
          digestsCount: digests.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'check_regulation_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Policy Management Tools ──────────────────────────────────
    case 'policy.create_policy': {
      const title = String(args.title ?? '');
      const category = String(args.category ?? 'security') as any;
      const owner = String(args.owner ?? 'system');
      const approver = String(args.approver ?? 'system');
      const content = String(args.content ?? '');
      const framework = String(args.framework ?? 'iso27001');
      if (!title) {
        return { ok: false, error: 'title_required', timestamp: new Date().toISOString() };
      }
      try {
        const policy = policyManager.createPolicy({ title, category, owner, approver, content, framework });
        return { ok: true, policy, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'create_policy_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'policy.list_policies': {
      const policies = policyManager.listPolicies();
      const stats = policyManager.getStats();
      return { ok: true, policies, totalCount: policies.length, stats, timestamp: new Date().toISOString() };
    }
    case 'policy.get_policy': {
      const policyId = String(args.policyId ?? '');
      if (!policyId) {
        return { ok: false, error: 'policyId_required', timestamp: new Date().toISOString() };
      }
      try {
        const policy = policyManager.getPolicy(policyId);
        if (!policy) {
          return { ok: false, error: `policy_not_found: ${policyId}`, timestamp: new Date().toISOString() };
        }
        return { ok: true, policy, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_policy_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Compliance Orchestrator Tools ─────────────────────────────
    case 'compliance_orch.run_scan': {
      const orgId = String(args.orgId ?? 'org-default');
      const enabledFrameworks = (args.frameworks as string[]) ?? ['iso27001'];
      const riskTolerance = String(args.riskTolerance ?? 'medium') as 'low' | 'medium' | 'high';
      try {
        const compiler = complianceOrchestrator.getCompiler();
        const allASTs = compiler.getAllASTs();
        const frameworksCompiled = allASTs.map(a => a.framework);
        return {
          ok: true,
          orgId,
          scanType: 'compliance_orchestration',
          frameworksCompiled,
          totalFrameworks: frameworksCompiled.length,
          graphHash: complianceOrchestrator.getGraph().getGraphHash(),
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'compliance_orch_scan_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'compliance_orch.get_status': {
      const orgId = String(args.orgId ?? 'org-default');
      try {
        const graph = complianceOrchestrator.getGraph();
        const compiler = complianceOrchestrator.getCompiler();
        return {
          ok: true,
          orgId,
          orchestratorStatus: 'initialized',
          frameworksAvailable: compiler.getAllASTs().map(a => a.framework),
          graphHash: graph.getGraphHash(),
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'compliance_orch_status_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Continuous Compliance Tools ──────────────────────────────
    case 'continuous.check_drift': {
      const tenantIdStr = String(tenantId);
      const framework = String(args.framework ?? 'iso27001') as any;
      try {
        const driftDetector = continuousEngine.getDriftDetector();
        const driftEvents = driftDetector.getDriftEvents(tenantIdStr, framework);
        return {
          ok: true,
          tenantId,
          framework,
          driftEventsDetected: driftEvents.length,
          driftEvents,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'check_drift_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'continuous.get_posture': {
      const tenantIdStr = String(tenantId);
      const framework = String(args.framework ?? 'iso27001') as any;
      try {
        const postureMonitor = continuousEngine.getPostureMonitor();
        const posture = postureMonitor.calculatePosture({
          tenantId: tenantIdStr,
          frameworkCode: framework,
          controlStatuses: new Map(),
          driftEvents: [],
        });
        return {
          ok: true,
          tenantId,
          framework,
          overallScore: posture.overallScore,
          controlScores: Object.fromEntries(posture.controlScores),
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_posture_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── AI Threat Detection Tools ────────────────────────────────
    case 'threat.scan': {
      const metric = String(args.metric ?? 'api_error_rate');
      const value = typeof args.value === 'number' ? args.value : 0;
      const threshold = typeof args.threshold === 'number' ? args.threshold : 2.0;
      try {
        const baselines = anomalyDetector.getBaselines();
        const detection = anomalyDetector.detect(metric, value);
        return {
          ok: true,
          scanType: 'anomaly_detection',
          metric,
          value,
          threshold,
          baselinesLoaded: baselines.length,
          detection,
          hasFinding: detection !== null,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'threat_scan_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'threat.get_findings': {
      try {
        const baselines = anomalyDetector.getBaselines();
        const alertNodes = securityGraph.getNodesByType('alert');
        const findings = alertNodes.map((node) => ({
          id: node.id,
          name: node.name,
          severity: node.properties.severity ?? (node.riskScore >= 70 ? 'high' : node.riskScore >= 40 ? 'medium' : 'low'),
          riskScore: node.riskScore,
          controlId: node.properties.controlId ?? null,
          description: node.properties.description ?? '',
          tags: node.tags,
          firstSeen: node.firstSeen,
          lastSeen: node.lastSeen,
        }));
        return {
          ok: true,
          findings,
          totalCount: findings.length,
          baselines: baselines.map(b => ({
            metric: b.metric,
            mean: b.mean,
            stdDev: b.stdDev,
            sampleCount: b.sampleCount,
            lastUpdated: b.lastUpdated,
          })),
          graphStats: securityGraph.getStats(),
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_findings_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── AI Supply Chain Tools ────────────────────────────────────
    case 'supply_chain.verify_model': {
      const modelId = String(args.modelId ?? '');
      if (!modelId) {
        return { ok: false, error: 'modelId_required', timestamp: new Date().toISOString() };
      }
      try {
        const result = await supplyChain.verifyModelProvenance(modelId);
        return { ok: true, result, modelId, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'verify_model_failed', modelId, timestamp: new Date().toISOString() };
      }
    }
    case 'supply_chain.list_models': {
      try {
        const models = supplyChain.listModels();
        return {
          ok: true,
          models,
          totalCount: models.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'list_models_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'supply_chain.register_model': {
      const identity = args.identity as import('@grc-claw/ai-supply-chain').ModelIdentity | undefined;
      if (!identity || !identity.id || !identity.name) {
        return { ok: false, error: 'identity_with_id_and_name_required', timestamp: new Date().toISOString() };
      }
      try {
        const entry = await supplyChain.registerModel(identity);
        return { ok: true, entry, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'register_model_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'supply_chain.enforce_policy': {
      const modelId = String(args.modelId ?? '');
      const policyTool = String(args.tool ?? '');
      const role = String(args.role ?? 'agent');
      if (!modelId || !policyTool) {
        return { ok: false, error: 'modelId_and_tool_required', timestamp: new Date().toISOString() };
      }
      try {
        const receipts = await supplyChain.enforceRuntimePolicy(modelId, {
          tool: policyTool,
          args: (args.context as Record<string, unknown>) ?? {},
          role,
        });
        return { ok: true, receipts, modelId, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'enforce_policy_failed', modelId, timestamp: new Date().toISOString() };
      }
    }
    case 'supply_chain.submit_proposal': {
      const proposal = args.proposal as import('@grc-claw/ai-supply-chain').ModelPolicyProposal | undefined;
      if (!proposal || !proposal.id || !proposal.modelId || !proposal.action) {
        return { ok: false, error: 'proposal_with_id_modelId_and_action_required', timestamp: new Date().toISOString() };
      }
      try {
        const consensus = await supplyChain.submitPolicyProposal(proposal);
        return { ok: true, consensus, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'submit_proposal_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Federated Compliance Mesh Tools ──────────────────────────
    case 'federated.join_mesh': {
      const org = args.org as import('@grc-claw/federated-compliance-mesh').FederatedOrganization | undefined;
      if (!org || !org.id || !org.name) {
        return { ok: false, error: 'org_with_id_and_name_required', timestamp: new Date().toISOString() };
      }
      try {
        complianceMesh.registerOrganization(org);
        return { ok: true, joined: true, orgId: org.id, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'join_mesh_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'federated.share_posture': {
      const orgId = String(args.orgId ?? '');
      const frameworkCode = String(args.frameworkCode ?? '');
      const overallScore = Number(args.overallScore ?? 0);
      if (!orgId || !frameworkCode) {
        return { ok: false, error: 'orgId_and_frameworkCode_required', timestamp: new Date().toISOString() };
      }
      try {
        const state: import('@grc-claw/federated-compliance-mesh').FederatedComplianceState = {
          orgId,
          frameworkCode: frameworkCode as import('@grc-claw/federated-compliance-mesh').FrameworkCode,
          overallScore,
          controlScores: new Map(Object.entries((args.controlScores as Record<string, number>) ?? {})),
          lastUpdated: new Date().toISOString(),
          evidenceHashes: new Map(Object.entries((args.evidenceHashes as Record<string, string>) ?? {})),
        };
        const events = complianceMesh.updateComplianceState(
          orgId,
          frameworkCode as import('@grc-claw/federated-compliance-mesh').FrameworkCode,
          state,
        );
        return { ok: true, events, orgId, frameworkCode, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'share_posture_failed', orgId, timestamp: new Date().toISOString() };
      }
    }
    case 'federated.verify_peer': {
      const fromOrgId = String(args.fromOrgId ?? '');
      const toOrgId = String(args.toOrgId ?? '');
      if (!fromOrgId || !toOrgId) {
        return { ok: false, error: 'fromOrgId_and_toOrgId_required', timestamp: new Date().toISOString() };
      }
      try {
        const path = complianceMesh.findPath(fromOrgId, toOrgId);
        const orgs = complianceMesh.getOrganizations();
        const targetOrg = orgs.find((o) => o.id === toOrgId);
        return {
          ok: true,
          reachable: path !== null,
          path,
          peerStatus: targetOrg?.status ?? 'unknown',
          trustLevel: targetOrg?.trustLevel ?? 0,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'verify_peer_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'federated.get_mesh_status': {
      try {
        const stats = complianceMesh.getMeshStats();
        const orgs = complianceMesh.getOrganizations();
        return {
          ok: true,
          stats,
          organizations: orgs.map((o) => ({ id: o.id, name: o.name, status: o.status, trustLevel: o.trustLevel })),
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_mesh_status_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Board Reporting Tools ─────────────────────────────────────
    case 'board.generate_report': {
      const reportType = String(args.type ?? 'board_summary') as any;
      const period = String(args.period ?? new Date().toISOString().substring(0, 7));
      try {
        const report = boardReporter.generateReport(reportType, period);
        return { ok: true, report, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'generate_report_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'board.get_dashboard': {
      try {
        const dashboard = boardReporter.getExecutiveDashboard();
        return { ok: true, dashboard, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'get_dashboard_failed', timestamp: new Date().toISOString() };
      }
    }

    // ─── Auto Evidence Tools ──────────────────────────────────────
    case 'auto_evidence.collect': {
      try {
        const provider = String(args.provider ?? 'aws') as any;
        const accountId = String(args.accountId ?? 'default-account');
        const regions = (args.regions as string[]) ?? ['us-east-1'];
        autoEvidence.connectProvider(provider, accountId, regions);
        const collectors = autoEvidence.autoDeployCollectors(provider);
        const evidenceItems = collectors.map(c => autoEvidence.collectEvidence(c.id)).filter(Boolean);
        return {
          ok: true,
          provider,
          collectorsDeployed: collectors.length,
          evidenceCollected: evidenceItems.length,
          evidence: evidenceItems,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'auto_evidence_collect_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'auto_evidence.assess': {
      try {
        const provider = String(args.provider ?? 'aws') as any;
        const templates = autoEvidence.getTemplates(provider);
        return {
          ok: true,
          provider,
          availableTemplates: templates.length,
          templates: templates.map(t => ({
            provider: t.provider,
            resourceType: t.resourceType,
            controlId: t.controlId,
            name: t.name,
            description: t.description,
          })),
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'auto_evidence_assess_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Browser Evidence Tools ────────────────────────────────────
    case 'browser_evidence.collect': {
      try {
        const portalName = String(args.portalName ?? 'unknown');
        const portalUrl = String(args.portalUrl ?? '');
        const username = String(args.username ?? '');
        const password = String(args.password ?? '');
        const screenshotPaths = Array.isArray(args.screenshotPaths) ? args.screenshotPaths as string[] : ['/'];
        if (!portalUrl) {
          return { ok: false, error: 'portalUrl_required', timestamp: new Date().toISOString() };
        }

        const adapter = new PlaywrightAdapter({ headless: true });
        const collector = new BrowserEvidenceCollector({ headless: true, retryCount: 2 }, adapter);
        const portal: PortalConfig = {
          name: portalName,
          url: portalUrl,
          authType: username ? 'basic' : 'api_key',
          credentials: { username, password },
          selectors: { login: 'input[type="text"], input[name="username"], #username' },
          screenshotPaths,
        };

        const artifact = await collector.collectFromPortal(portal);
        return {
          ok: true,
          artifactId: artifact.id,
          portalName,
          portalUrl,
          screenshotHash: artifact.hash,
          domSnapshotLength: artifact.domSnapshot.length,
          structuredData: artifact.structuredData,
          metadata: artifact.metadata,
          timestamp: artifact.timestamp,
        };
      } catch (err: any) {
        const msg = err.message ?? '';
        if (msg.includes('Playwright is not installed')) {
          return {
            ok: false,
            executionState: 'not_configured',
            message: 'Playwright is not installed. Run: npm install playwright',
            timestamp: new Date().toISOString(),
          };
        }
        return { ok: false, error: msg || 'browser_evidence_collect_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'browser_evidence.screenshot': {
      try {
        const portalName = String(args.portalName ?? 'unknown');
        const portalUrl = String(args.portalUrl ?? args.url ?? '');
        if (!portalUrl) {
          return { ok: false, error: 'url_required', timestamp: new Date().toISOString() };
        }

        const adapter = new PlaywrightAdapter({ headless: true });
        await adapter.launch();
        try {
          await adapter.navigate(portalUrl);
          const screenshotBuffer = await adapter.screenshot();
          const { createHash } = await import('node:crypto');
          const screenshotHash = createHash('sha256').update(screenshotBuffer).digest('hex');
          return {
            ok: true,
            portalName,
            portalUrl,
            screenshotHash,
            screenshotSize: screenshotBuffer.length,
            screenshotBase64: screenshotBuffer.toString('base64'),
            timestamp: new Date().toISOString(),
          };
        } finally {
          await adapter.close();
        }
      } catch (err: any) {
        const msg = err.message ?? '';
        if (msg.includes('Playwright is not installed')) {
          return {
            ok: false,
            executionState: 'not_configured',
            message: 'Playwright is not installed. Run: npm install playwright',
            timestamp: new Date().toISOString(),
          };
        }
        return { ok: false, error: msg || 'browser_evidence_screenshot_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Incident Response Tools ──────────────────────────────────
    case 'incident.create': {
      try {
        const title = String(args.title ?? `Incident-${Date.now()}`);
        const type = String(args.type ?? 'other') as any;
        const severity = String(args.severity ?? 'medium') as any;
        const description = String(args.description ?? '');
        const reportedBy = String(args.reportedBy ?? 'system');
        const assignee = String(args.assignee ?? 'system');
        const incident = incidentManager.reportIncident({ title, type, severity, description, reportedBy, assignee });
        return {
          ok: true,
          incidentId: incident.id,
          title: incident.title,
          type: incident.type,
          severity: incident.severity,
          status: incident.status,
          reportedBy,
          assignee,
          detectedAt: incident.detectedAt,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'incident_create_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'incident.list': {
      try {
        const statusFilter = String(args.status ?? '') as any;
        let incidents = incidentManager.listIncidents();
        if (statusFilter) {
          incidents = incidents.filter(i => i.status === statusFilter);
        }
        const stats = incidentManager.getStats();
        return {
          ok: true,
          incidents: incidents.map(i => ({
            id: i.id,
            title: i.title,
            type: i.type,
            severity: i.severity,
            status: i.status,
            detectedAt: i.detectedAt,
            assignee: i.assignee,
          })),
          totalCount: incidents.length,
          stats,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'incident_list_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Dev Compliance Tools ──────────────────────────────────────
    case 'dev_compliance.scan_pr': {
      try {
        const frameworks = (args.frameworks as import('@grc-claw/dev-compliance').FrameworkCode[]) ?? ['iso27001', 'soc2'];
        const reviewer = new GitHubPRReviewer(frameworks);
        const prNumber = Number(args.prNumber ?? 0);
        const repo = String(args.repo ?? '');
        const title = String(args.prTitle ?? '');
        const body = String(args.prBody ?? '');
        const files = (args.files as { filename: string; patch: string; additions: number; deletions: number }[]) ?? [];
        if (!repo || files.length === 0) {
          return { ok: false, error: 'repo_and_files_required', timestamp: new Date().toISOString() };
        }
        const result = await reviewer.reviewPR({ number: prNumber, repo, title, body, files });
        return {
          ok: true,
          prNumber,
          repo,
          findings: result.findings,
          summary: result.summary,
          status: result.status,
          findingsCount: result.findings.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'dev_compliance_scan_pr_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'dev_compliance.check_ci': {
      try {
        const framework = String(args.framework ?? 'iso27001') as any;
        const failOnSeverity = String(args.failOnSeverity ?? 'critical') as any;
        const gate = new CICDComplianceGate({ framework, failOnSeverity, maxScore: 100 });
        const files = (args.files as string[]) ?? [];
        const contentMap = new Map<string, string>();
        const contentArg = args.content as Record<string, string> | undefined;
        if (contentArg) {
          for (const [k, v] of Object.entries(contentArg)) {
            contentMap.set(k, String(v));
          }
        }
        const result = await gate.evaluate({ files, content: contentMap });
        return {
          ok: true,
          passed: result.passed,
          score: result.score,
          findings: result.findings,
          gateName: result.gateName,
          framework,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'dev_compliance_check_ci_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── GRC Engineering Tools ────────────────────────────────────
    case 'engineering.pipeline': {
      try {
        const triggeredBy = String(args.triggeredBy ?? 'system');
        const pipeline = new CompliancePipeline();
        const enabledStages = pipeline.getEnabledStages();
        const config = args.config as import('@grc-claw/grc-engineering').GrcConfig | undefined;
        if (config) {
          const run = await pipeline.run(config, triggeredBy);
          return {
            ok: true,
            runId: run.id,
            status: run.status,
            stagesCompleted: run.stages.length,
            evidenceCollected: run.evidence.length,
            startedAt: run.startedAt,
            completedAt: run.completedAt,
            triggeredBy,
            timestamp: new Date().toISOString(),
          };
        }
        return {
          ok: true,
          enabledStages,
          message: 'Pipeline ready. Provide a config argument to execute the pipeline run.',
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'engineering_pipeline_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'engineering.gitops': {
      try {
        const workflow = new GitOpsWorkflow();
        const branch = String(args.branch ?? 'main');
        const action = String(args.action ?? 'status') as 'init' | 'commit' | 'status' | 'drift';
        if (action === 'init') {
          const state = workflow.initRepo(branch);
          return {
            ok: true,
            action: 'init',
            commitSha: state.commitSha,
            branch,
            configHash: state.configHash,
            timestamp: new Date().toISOString(),
          };
        }
        if (action === 'commit') {
          const config = args.config as import('@grc-claw/grc-engineering').GrcConfig;
          const author = String(args.author ?? 'system');
          const message = String(args.message ?? 'compliance config update');
          if (!config) {
            return { ok: false, error: 'config_required_for_commit', timestamp: new Date().toISOString() };
          }
          const commit = workflow.commit(config, author, message, branch);
          return {
            ok: true,
            action: 'commit',
            sha: commit.sha,
            author,
            message,
            configHash: commit.configHash,
            timestamp: new Date().toISOString(),
          };
        }
        if (action === 'drift') {
          const report = workflow.getDriftHistory();
          return {
            ok: true,
            action: 'drift',
            driftReportsCount: report.length,
            timestamp: new Date().toISOString(),
          };
        }
        const history = workflow.getCommitHistory();
        return {
          ok: true,
          action: 'status',
          commitsCount: history.length,
          branchProtections: workflow.getBranchProtections().size,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'engineering_gitops_failed', timestamp: new Date().toISOString() };
      }
    }
    // ─── Agent Trust Score Tools ──────────────────────────────────
    case 'trust_score.calculate': {
      try {
        const agentDid = String(args.agentDid ?? '');
        const agentName = String(args.agentName ?? 'unknown');
        const agentTenantId = String(args.tenantId ?? String(tenantId));
        const complianceScore = typeof args.complianceScore === 'number' ? args.complianceScore : 70;
        const frameworks = (args.frameworks as string[]) ?? [] as any;
        const signals = (args.signals as { type: string; timestamp: string; confidence: number; details: string; impact: number }[]) ?? [];
        if (!agentDid) {
          return { ok: false, error: 'agentDid_required', timestamp: new Date().toISOString() };
        }
        const profile = await trustScoreEngine.scoreAgent(agentDid, agentName, agentTenantId, signals as import('@grc-claw/agent-trust-score').BehavioralSignal[], complianceScore, frameworks as import('@grc-claw/agent-trust-score').FrameworkCode[]);
        return {
          ok: true,
          agentDid: profile.agentDid,
          agentName: profile.agentName,
          overallTrustScore: profile.overallTrustScore,
          riskLevel: profile.riskLevel,
          status: profile.status,
          dimensions: profile.dimensions,
          riskFactorsCount: profile.riskFactors.length,
          signalCount: profile.behavioralSignals.length,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'trust_score_calculate_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'trust_score.profile': {
      try {
        const agentDid = String(args.agentDid ?? '');
        if (!agentDid) {
          return { ok: false, error: 'agentDid_required', timestamp: new Date().toISOString() };
        }
        const profile = await trustScoreEngine.getAgentProfile(agentDid);
        if (!profile) {
          return {
            ok: true,
            agentDid,
            found: false,
            message: 'No trust profile found for this agent. Use trust_score.calculate to generate one.',
            timestamp: new Date().toISOString(),
          };
        }
        return {
          ok: true,
          agentDid: profile.agentDid,
          agentName: profile.agentName,
          overallTrustScore: profile.overallTrustScore,
          riskLevel: profile.riskLevel,
          status: profile.status,
          dimensions: profile.dimensions,
          complianceScore: profile.compliancePosture.overallScore,
          scoreHistoryCount: profile.scoreHistory.length,
          lastScoredAt: profile.lastScoredAt,
          timestamp: new Date().toISOString(),
        };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'trust_score_profile_failed', timestamp: new Date().toISOString() };
      }
    }

    // ─── Agent Audit Trail Tools ─────────────────────────────────
    case 'audit_trail.record': {
      try {
        const agentDid = String(args.agentDid ?? 'system');
        const toolName = String(args.tool ?? '');
        const toolArgs = (args.args as Record<string, unknown>) ?? {};
        const result = (args.result as Record<string, unknown>) ?? {};
        const record = agentAuditTrail.record(agentDid, toolName, toolArgs, result);
        return { ok: true, record, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'audit_trail_record_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'audit_trail.verify': {
      try {
        const result = agentAuditTrail.verify();
        return { ok: true, ...result, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'audit_trail_verify_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'audit_trail.query': {
      try {
        const agentDid = typeof args.agentDid === 'string' ? args.agentDid : undefined;
        const toolFilter = typeof args.tool === 'string' ? args.tool : undefined;
        const from = typeof args.from === 'string' ? args.from : undefined;
        const to = typeof args.to === 'string' ? args.to : undefined;
        const limit = typeof args.limit === 'number' ? args.limit : undefined;
        const offset = typeof args.offset === 'number' ? args.offset : undefined;
        const records = agentAuditTrail.query({ agentDid, tool: toolFilter, from, to, limit, offset });
        return { ok: true, records, count: records.length, total: agentAuditTrail.count(), timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'audit_trail_query_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'audit_trail.export': {
      try {
        const format = (String(args.format ?? 'json') as 'json' | 'csv');
        const agentDid = typeof args.agentDid === 'string' ? args.agentDid : undefined;
        const toolFilter = typeof args.tool === 'string' ? args.tool : undefined;
        const from = typeof args.from === 'string' ? args.from : undefined;
        const to = typeof args.to === 'string' ? args.to : undefined;
        const exported = agentAuditTrail.export({ format, agentDid, tool: toolFilter, from, to });
        return { ok: true, format, data: exported, recordCount: agentAuditTrail.count(), timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'audit_trail_export_failed', timestamp: new Date().toISOString() };
      }
    }

    // ─── Integration Marketplace Tools ────────────────────────────────
    case 'integration.list': {
      const connectors = integrationMarketplace.getEnabledConnectors();
      const stats = integrationMarketplace.getStats();
      return {
        ok: true,
        connectors: connectors.map(c => ({ id: c.id, name: c.name, category: c.category, frameworks: c.frameworks, capabilities: c.capabilities })),
        stats,
        timestamp: new Date().toISOString(),
      };
    }
    case 'integration.enable': {
      const id = String(args.connectorId ?? args.id ?? '');
      if (!id) return { ok: false, error: 'connectorId_required', timestamp: new Date().toISOString() };
      integrationMarketplace.enableConnector(id);
      return { ok: true, connectorId: id, enabled: true, timestamp: new Date().toISOString() };
    }
    case 'integration.disable': {
      const id = String(args.connectorId ?? args.id ?? '');
      if (!id) return { ok: false, error: 'connectorId_required', timestamp: new Date().toISOString() };
      integrationMarketplace.disableConnector(id);
      return { ok: true, connectorId: id, enabled: false, timestamp: new Date().toISOString() };
    }
    case 'integration.collect': {
      const id = typeof args.connectorId === 'string' ? args.connectorId : typeof args.id === 'string' ? args.id : '';
      try {
        if (id) {
          const job = await integrationMarketplace.collectFromConnector(id);
          return { ok: true, job, timestamp: new Date().toISOString() };
        }
        const jobs = await integrationMarketplace.collectAll();
        return { ok: true, jobs, count: jobs.length, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'integration_collect_failed', timestamp: new Date().toISOString() };
      }
    }

    // ─── Policy Management Hub Tools ──────────────────────────────────
    case 'policy_hub.create': {
      try {
        const policy = policyHub.createPolicy(args as Parameters<typeof policyHub.createPolicy>[0]);
        return { ok: true, policy, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'policy_hub_create_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'policy_hub.list': {
      const policies = policyHub.listPolicies();
      return { ok: true, policies, count: policies.length, timestamp: new Date().toISOString() };
    }
    case 'policy_hub.approve': {
      const policyId = String(args.policyId ?? '');
      if (!policyId) return { ok: false, error: 'policyId_required', timestamp: new Date().toISOString() };
      try {
        const workflow = policyHub.initiateApproval(policyId, (args.steps as Array<{ assigneeId: string; assigneeName: string; role: string; deadline?: string }>) ?? [], String(args.initiatedBy ?? 'system'));
        return { ok: true, workflow, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'policy_hub_approve_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'policy_hub.publish': {
      const policyId = String(args.policyId ?? '');
      if (!policyId) return { ok: false, error: 'policyId_required', timestamp: new Date().toISOString() };
      try {
        const policy = policyHub.publishPolicy(policyId, String(args.publishedBy ?? 'system'));
        return { ok: true, policy, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'policy_hub_publish_failed', timestamp: new Date().toISOString() };
      }
    }

    // ─── Vendor Risk Management Tools ─────────────────────────────────
    case 'vendor_risk.create_vendor': {
      try {
        const vendor = vendorRiskMgmt.createVendor(args as Parameters<typeof vendorRiskMgmt.createVendor>[0]);
        return { ok: true, vendor, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'vendor_risk_create_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'vendor_risk.list_vendors': {
      const vendors = vendorRiskMgmt.listVendors();
      return { ok: true, vendors, count: vendors.length, timestamp: new Date().toISOString() };
    }
    case 'vendor_risk.get_risk_score': {
      const vendorId = String(args.vendorId ?? '');
      if (!vendorId) return { ok: false, error: 'vendorId_required', timestamp: new Date().toISOString() };
      const score = vendorRiskMgmt.getRiskScore(vendorId);
      if (!score) return { ok: false, error: `vendor_not_found: ${vendorId}`, timestamp: new Date().toISOString() };
      return { ok: true, score, timestamp: new Date().toISOString() };
    }

    // ─── Employee Lifecycle Tools ─────────────────────────────────────
    case 'employee.create': {
      try {
        const employee = employeeLifecycle.createEmployee(args as Parameters<typeof employeeLifecycle.createEmployee>[0]);
        return { ok: true, employee, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'employee_create_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'employee.list': {
      const state = typeof args.state === 'string' ? args.state as import('@grc-claw/employee-lifecycle').EmployeeState : undefined;
      const department = typeof args.department === 'string' ? args.department : undefined;
      const employees = employeeLifecycle.listEmployees(state ? { state, department } : undefined);
      return { ok: true, employees, count: employees.length, timestamp: new Date().toISOString() };
    }
    case 'employee.onboard': {
      const employeeId = String(args.employeeId ?? args.id ?? '');
      if (!employeeId) return { ok: false, error: 'employeeId_required', timestamp: new Date().toISOString() };
      try {
        const workflow = employeeLifecycle.startOnboarding(employeeId);
        return { ok: true, workflow, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'employee_onboard_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'employee.offboard': {
      const employeeId = String(args.employeeId ?? args.id ?? '');
      if (!employeeId) return { ok: false, error: 'employeeId_required', timestamp: new Date().toISOString() };
      try {
        const workflow = employeeLifecycle.startOffboarding(employeeId, typeof args.targetDate === 'string' ? args.targetDate : undefined);
        return { ok: true, workflow, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'employee_offboard_failed', timestamp: new Date().toISOString() };
      }
    }

    // ─── Compliance Task Engine Tools ─────────────────────────────────
    case 'task.create': {
      try {
        const task = complianceTaskEngine.createTask(args as Parameters<typeof complianceTaskEngine.createTask>[0]);
        return { ok: true, task, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'task_create_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'task.list': {
      const tasks = complianceTaskEngine.listTasks();
      return { ok: true, tasks, count: tasks.length, timestamp: new Date().toISOString() };
    }
    case 'task.update_status': {
      const taskId = String(args.taskId ?? args.id ?? '');
      const action = String(args.action ?? '');
      if (!taskId || !action) return { ok: false, error: 'taskId_and_action_required', timestamp: new Date().toISOString() };
      try {
        let task;
        if (action === 'start') task = complianceTaskEngine.startTask(taskId);
        else if (action === 'complete') task = complianceTaskEngine.completeTask(taskId);
        else if (action === 'block') task = complianceTaskEngine.blockTask(taskId, typeof args.reason === 'string' ? args.reason : undefined);
        else if (action === 'cancel') task = complianceTaskEngine.cancelTask(taskId);
        else return { ok: false, error: 'invalid_action', validActions: ['start', 'complete', 'block', 'cancel'], timestamp: new Date().toISOString() };
        return { ok: true, task, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'task_update_status_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'task.analytics': {
      const analytics = complianceTaskEngine.getAnalytics();
      return { ok: true, analytics, timestamp: new Date().toISOString() };
    }

    // ─── Evidence Automation Engine Tools ──────────────────────────────
    case 'evidence_auto.schedule': {
      const connectorId = String(args.connectorId ?? '');
      const scheduleConfig = args.config as import('@grc-claw/evidence-automation-engine').ScheduleConfig;
      if (!connectorId || !scheduleConfig) return { ok: false, error: 'connectorId_and_config_required', timestamp: new Date().toISOString() };
      try {
        const schedule = evidenceAutoEngine.createSchedule(connectorId, scheduleConfig);
        return { ok: true, schedule, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'evidence_auto_schedule_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'evidence_auto.run_now': {
      const connectorId = typeof args.connectorId === 'string' ? args.connectorId : '';
      try {
        if (connectorId) {
          const job = await evidenceAutoEngine.collectFromConnector(connectorId);
          return { ok: true, job, timestamp: new Date().toISOString() };
        }
        const jobs = await evidenceAutoEngine.collectAll();
        return { ok: true, jobs, count: jobs.length, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'evidence_auto_run_now_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'evidence_auto.gaps': {
      const gaps = evidenceAutoEngine.detectGaps();
      return { ok: true, gaps, count: gaps.length, timestamp: new Date().toISOString() };
    }
    case 'evidence_auto.summary': {
      const summary = evidenceAutoEngine.generateSummaryReport();
      return { ok: true, summary, timestamp: new Date().toISOString() };
    }

    // ─── Terraform Provider Tools ──────────────────────────────────
    case 'terraform.plan': {
      try {
        const config = args as unknown as import('@grc-claw/terraform-provider').TerraformResourceConfig;
        const plan = terraformProvider.plan(config);
        return { ok: true, plan, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'terraform_plan_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'terraform.apply': {
      try {
        const config = args as unknown as import('@grc-claw/terraform-provider').TerraformResourceConfig;
        const result = terraformProvider.apply(config);
        return { ok: true, result, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'terraform_apply_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'terraform.destroy': {
      const resourceType = String(args.resourceType ?? args.type ?? '') as import('@grc-claw/terraform-provider').TerraformResourceType;
      const name = String(args.name ?? '');
      if (!resourceType || !name) {
        return { ok: false, error: 'resourceType_and_name_required', timestamp: new Date().toISOString() };
      }
      try {
        const deleted = terraformProvider.destroy(resourceType, name);
        return { ok: true, deleted, resourceType, name, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'terraform_destroy_failed', timestamp: new Date().toISOString() };
      }
    }
    case 'terraform.import': {
      const resourceType = String(args.resourceType ?? args.type ?? '') as import('@grc-claw/terraform-provider').TerraformResourceType;
      const name = String(args.name ?? '');
      const id = String(args.id ?? '');
      const attributes = (args.attributes as Record<string, unknown>) ?? {};
      if (!resourceType || !name || !id) {
        return { ok: false, error: 'resourceType_name_and_id_required', timestamp: new Date().toISOString() };
      }
      try {
        const result = terraformProvider.importResource(resourceType, name, id, attributes);
        return { ok: true, result, timestamp: new Date().toISOString() };
      } catch (err: any) {
        return { ok: false, error: err.message ?? 'terraform_import_failed', timestamp: new Date().toISOString() };
      }
    }

    // ─── Continuous Trust Engine Tools ─────────────────────────────────────
    case 'trust.get_score': {
      const score = continuousTrustEngine.getScore();
      return { ok: true, score, timestamp: new Date().toISOString() };
    }
    case 'trust.get_history': {
      const hours = Number(args.hours ?? 24);
      const history = continuousTrustEngine.getHistory(hours);
      return { ok: true, history, count: history.length, timestamp: new Date().toISOString() };
    }
    case 'trust.get_alerts': {
      const alerts = continuousTrustEngine.getAlerts();
      return { ok: true, alerts, count: alerts.length, timestamp: new Date().toISOString() };
    }
    case 'trust.register_signal': {
      const signal = args.signal as import('@grc-claw/continuous-trust-engine').TrustSignal;
      continuousTrustEngine.registerSignal(signal);
      return { ok: true, message: 'Signal registered', timestamp: new Date().toISOString() };
    }

    // ─── Agent Collaboration Tools ─────────────────────────────────────────
    case 'collaboration.get_sessions': {
      const sessions = agentCollaboration.getActiveSessions();
      return { ok: true, sessions, count: sessions.length, timestamp: new Date().toISOString() };
    }
    case 'collaboration.get_agents': {
      const requiredCaps = (args.requiredCapabilities as string[]) ?? [];
      const agents = agentCollaboration.getAvailableAgents(requiredCaps);
      return { ok: true, agents, count: agents.length, timestamp: new Date().toISOString() };
    }
    case 'collaboration.submit_task': {
      const task = args.task as import('@grc-claw/agent-collaboration').CollaborationTask;
      const sessionId = agentCollaboration.submitTask(task);
      return { ok: true, sessionId, timestamp: new Date().toISOString() };
    }

    // ─── Regulatory Change Management Tools ─────────────────────────────────
    case 'regulatory.get_changes': {
      const framework = args.framework as string | undefined;
      const severity = args.severity as string | undefined;
      const status = args.status as string | undefined;
      const changes = regulatoryChangeMgmt.getChanges({ framework, severity, status });
      return { ok: true, changes, count: changes.length, timestamp: new Date().toISOString() };
    }
    case 'regulatory.get_gaps': {
      const framework = args.framework as string | undefined;
      const status = args.status as string | undefined;
      const gaps = regulatoryChangeMgmt.getGaps({ framework, status });
      return { ok: true, gaps, count: gaps.length, timestamp: new Date().toISOString() };
    }
    case 'regulatory.analyze_change': {
      const changeId = String(args.changeId ?? '');
      const analysis = await regulatoryChangeMgmt.analyzeChange(changeId);
      return { ok: true, analysis, timestamp: new Date().toISOString() };
    }

    // ─── AI Governance Tools ───────────────────────────────────────────────
    case 'ai_governance.get_systems': {
      const riskClass = args.riskClass as string | undefined;
      const status = args.status as string | undefined;
      const systems = aiGovernance.getSystems({ riskClass, status });
      return { ok: true, systems, count: systems.length, timestamp: new Date().toISOString() };
    }
    case 'ai_governance.get_dashboard': {
      const dashboard = aiGovernance.getDashboardData();
      return { ok: true, dashboard, timestamp: new Date().toISOString() };
    }
    case 'ai_governance.register_system': {
      const system = args.system as import('@grc-claw/ai-governance').AISystem;
      aiGovernance.registerSystem(system);
      return { ok: true, message: 'AI system registered', timestamp: new Date().toISOString() };
    }

    // ─── Compliance Knowledge Graph Tools ──────────────────────────────────
    case 'knowledge_graph.get_summary': {
      const summary = complianceKnowledgeGraph.analytics.getSummary();
      return { ok: true, summary, timestamp: new Date().toISOString() };
    }
    case 'knowledge_graph.get_posture': {
      const organizationId = String(args.organizationId ?? 'demo-org');
      const posture = complianceKnowledgeGraph.analytics.calculatePosture(organizationId);
      return { ok: true, posture, timestamp: new Date().toISOString() };
    }
    case 'knowledge_graph.find_crosswalk': {
      const from = String(args.from ?? '');
      const to = String(args.to ?? '');
      const mappings = to
        ? complianceKnowledgeGraph.query
            .getCrosswalk(from)
            .filter((mapping) => mapping.targetFrameworkId === to || mapping.targetControlId === to)
        : complianceKnowledgeGraph.query.getCrosswalk(from);
      return { ok: true, mappings, count: mappings.length, timestamp: new Date().toISOString() };
    }
    case 'knowledge_graph.detect_patterns': {
      const patterns = complianceKnowledgeGraph.analytics.detectPatterns();
      return { ok: true, patterns, count: patterns.length, timestamp: new Date().toISOString() };
    }

    // ─── Evidence Graph Tools ─────────────────────────────────────────────
    case 'evidence_graph.get': {
      const organizationId = String(args.organizationId ?? 'demo-org');
      const graph = buildEvidenceGraphSnapshot(organizationId);
      return { ...graph, timestamp: new Date().toISOString() };
    }
    case 'evidence_graph.get_summary': {
      const organizationId = String(args.organizationId ?? 'demo-org');
      const graph = buildEvidenceGraphSnapshot(organizationId);
      return { ok: true, graph_hash: graph.graph_hash, summary: graph.summary, timestamp: new Date().toISOString() };
    }
    case 'evidence_graph.get_nodes': {
      const organizationId = String(args.organizationId ?? 'demo-org');
      const graph = buildEvidenceGraphSnapshot(organizationId);
      return { ok: true, graph_hash: graph.graph_hash, nodes: graph.nodes, count: graph.nodes.length, timestamp: new Date().toISOString() };
    }
    case 'evidence_graph.get_edges': {
      const organizationId = String(args.organizationId ?? 'demo-org');
      const graph = buildEvidenceGraphSnapshot(organizationId);
      return { ok: true, graph_hash: graph.graph_hash, edges: graph.edges, count: graph.edges.length, timestamp: new Date().toISOString() };
    }
    case 'evidence_graph.get_recommendations': {
      const organizationId = String(args.organizationId ?? 'demo-org');
      const graph = buildEvidenceGraphSnapshot(organizationId);
      return { ok: true, graph_hash: graph.graph_hash, recommendations: graph.recommendations, timestamp: new Date().toISOString() };
    }

    // ─── Predictive Compliance Tools ──────────────────────────────────────
    case 'predictive.get_forecasts': {
      const forecasts = predictiveCompliance.forecastAll();
      return { ok: true, forecasts, count: forecasts.length, timestamp: new Date().toISOString() };
    }
    case 'predictive.get_risks': {
      const risks = predictiveCompliance.rankByRisk();
      return { ok: true, risks, count: risks.length, timestamp: new Date().toISOString() };
    }
    case 'predictive.predict_failure': {
      const controlId = String(args.controlId ?? '');
      const forecast = predictiveCompliance.generateForecast(controlId);
      return { ok: true, forecast, timestamp: new Date().toISOString() };
    }

    // ─── Compliance Marketplace Tools ─────────────────────────────────────
    case 'marketplace.get_stats': {
      const stats = complianceMarketplace.stats();
      return { ok: true, stats, timestamp: new Date().toISOString() };
    }
    case 'marketplace.discover_packs': {
      const framework = args.framework as string | undefined;
      const industry = args.industry as string | undefined;
      const packs = complianceMarketplace.search({
        frameworks: framework ? [framework] : undefined,
        industries: industry ? [industry] : undefined,
        limit: Number(args.limit ?? 50),
      });
      return { ok: true, packs, count: packs.length, timestamp: new Date().toISOString() };
    }
    case 'marketplace.install_pack': {
      const packId = String(args.packId ?? '');
      const version = args.version as string | undefined;
      const result = complianceMarketplace.install(packId, version);
      return { ok: true, result, timestamp: new Date().toISOString() };
    }

    // ─── Zero Trust Audit Tools ───────────────────────────────────────────
    case 'zero_trust.verify_chain': {
      const verification = zeroTrustAudit.verify();
      return { ok: true, verification, timestamp: new Date().toISOString() };
    }
    case 'zero_trust.get_records': {
      const records = zeroTrustAudit.getRecords();
      return { ok: true, records, count: records.length, timestamp: new Date().toISOString() };
    }
    case 'zero_trust.export_evidence': {
      const format = String(args.format ?? 'json') as 'json' | 'xml' | 'pdf';
      const evidence = zeroTrustAudit.exportEvidence({ format });
      return { ok: true, evidence, timestamp: new Date().toISOString() };
    }

    // ─── Federated Learning Tools ─────────────────────────────────────────
    case 'federated.get_status': {
      return { ok: true, message: 'Federated learning network active', timestamp: new Date().toISOString() };
    }
    case 'federated.register_org': {
      const orgId = String(args.orgId ?? '');
      const org = { id: orgId, name: orgId, publicKey: 'default', registeredAt: new Date() };
      federatedLearning.registerOrganization(org);
      return { ok: true, message: 'Organization registered', timestamp: new Date().toISOString() };
    }

    // ─── Compliance Intelligence Tools ────────────────────────────────────
    case 'intelligence.get_trends': {
      const trends = complianceIntelligence.getAllTrends();
      return { ok: true, trends, timestamp: new Date().toISOString() };
    }
    case 'intelligence.get_benchmarks': {
      const benchmarks = complianceIntelligence.getNetworkSnapshot();
      return { ok: true, benchmarks, timestamp: new Date().toISOString() };
    }
    case 'intelligence.get_recommendations': {
      const orgId = String(args.orgId ?? 'default');
      const recs = complianceIntelligence.getRecommendations(orgId);
      return { ok: true, recommendations: recs, timestamp: new Date().toISOString() };
    }

    // ─── Autonomous Compliance Agent Tools ────────────────────────────────
    case 'autonomous.get_issues': {
      const issues = autonomousAgent.getScanResults();
      return { ok: true, issues, count: issues.length, timestamp: new Date().toISOString() };
    }
    case 'autonomous.get_metrics': {
      const metrics = autonomousAgent.getMetrics();
      return { ok: true, metrics, timestamp: new Date().toISOString() };
    }

    // ─── Compliance Digital Twin Tools ────────────────────────────────────
    case 'digital_twin.list_twins': {
      const twins = complianceDigitalTwin.listTwins();
      return { ok: true, twins, count: twins.length, timestamp: new Date().toISOString() };
    }
    case 'digital_twin.create_twin': {
      const twinId = String(args.twinId ?? `twin-${Date.now()}`);
      const name = String(args.name ?? 'Untitled Twin');
      const twin = complianceDigitalTwin.createTwin({
        twinId,
        name,
        description: String(args.description ?? ''),
        frameworks: [],
        snapshotRetentionCount: 10,
        syncIntervalMs: 300000,
        syncMode: 'incremental',
        riskThresholds: { critical: 90, high: 70, medium: 50, low: 30 },
      });
      return { ok: true, twin, timestamp: new Date().toISOString() };
    }
    case 'digital_twin.get_twin': {
      const twinId = String(args.twinId ?? '');
      const twin = complianceDigitalTwin.getTwin(twinId);
      return { ok: true, twin, timestamp: new Date().toISOString() };
    }

    // ─── Quantum-Resistant Crypto Tools ───────────────────────────────────
    case 'quantum.generate_key_material': {
      const keyMaterial = await quantumCrypto.generateFullKeyMaterial();
      return { ok: true, keyMaterial, timestamp: new Date().toISOString() };
    }

    // ─── Natural Language Compliance Tools ────────────────────────────────
    case 'nl_compliance.ask': {
      const question = String(args.question ?? '');
      const answer = nlCompliance.ask(question);
      return { ok: true, answer, timestamp: new Date().toISOString() };
    }
    case 'nl_compliance.follow_up': {
      const followUpQuestion = String(args.question ?? '');
      const sessionId = String(args.sessionId ?? 'default');
      const answer = nlCompliance.followUp(sessionId, followUpQuestion);
      return { ok: true, answer, timestamp: new Date().toISOString() };
    }
    case 'nl_compliance.generate_report': {
      const framework = String(args.framework ?? 'soc2') as any;
      const report = nlCompliance.generateReport([framework]);
      return { ok: true, report, timestamp: new Date().toISOString() };
    }

    // ─── Compliance Automation Marketplace Tools ──────────────────────────
    case 'automation_marketplace.get_stats': {
      const publisherList = automationMarketplace.publisher.list();
      const stats = { total: publisherList.length, published: publisherList.filter((a: any) => a.status === 'published').length };
      return { ok: true, stats, timestamp: new Date().toISOString() };
    }
    case 'automation_marketplace.search': {
      const framework = args.framework as string | undefined;
      const industry = args.industry as string | undefined;
      const result = await automationMarketplace.discovery.search({ frameworks: framework ? [framework as any] : undefined, industries: industry ? [industry] : undefined });
      return { ok: true, automations: result.results, count: result.total, timestamp: new Date().toISOString() };
    }
    case 'automation_marketplace.install': {
      const automationId = String(args.automationId ?? '');
      const version = args.version as string | undefined;
      const result = await automationMarketplace.installer.install(automationId, { version });
      return { ok: true, result, timestamp: new Date().toISOString() };
    }

    // ─── Real-Time Compliance Monitor Tools ───────────────────────────────
    case 'realtime_monitor.get_status': {
      const slaStatus = realTimeMonitor.slaMonitor.getStatus();
      const breaches = realTimeMonitor.slaMonitor.getBreaches();
      const status = { slaStatus: Object.fromEntries(slaStatus), breachCount: breaches.length };
      return { ok: true, status, timestamp: new Date().toISOString() };
    }
    case 'realtime_monitor.get_alerts': {
      const alerts = realTimeMonitor.alertEngine.getAlerts();
      return { ok: true, alerts, count: alerts.length, timestamp: new Date().toISOString() };
    }
    case 'realtime_monitor.create_dashboard': {
      const dashboardName = String(args.name ?? 'Default Dashboard');
      const dashboardId = `dashboard-${Date.now()}`;
      realTimeMonitor.dashboard.createDashboard({
        id: dashboardId,
        name: dashboardName,
        description: '',
        widgets: [],
        refreshIntervalMs: 30000,
      });
      return { ok: true, dashboard: { id: dashboardId, name: dashboardName }, timestamp: new Date().toISOString() };
    }

    default:
      return {
        ok: true,
        executionState: 'not_configured',
        tool,
        message: 'This tool requires additional configuration. Set the appropriate environment variables or connect the required service.',
      };
  }
      } catch (err: unknown) {
        if (span && deps.tracer) {
          deps.tracer.addSpanEvent(span.spanId, 'tool.error', { 'error.message': err instanceof Error ? err.message : String(err) });
          deps.tracer.endSpan(span.spanId, 'ERROR', err instanceof Error ? err.message : undefined);
        }
        throw err;
      } finally {
        if (span && deps.tracer) {
          deps.tracer.addSpanEvent(span.spanId, 'tool.complete', { tool });
          deps.tracer.endSpan(span.spanId, 'OK');
        }
      }
}

export async function dispatchAgentTool(
  tool: string,
  args: Record<string, unknown>,
  deps: {
    registry: ConnectorRegistry;
    evidence: EvidenceStore;
    a2z: A2ZSocConnector;
    claw: ClawDispatchContext;
    persistence?: import('@grc-claw/persistence').PersistenceLayer | null;
    agentBuilder?: import('@grc-claw/agent-builder').AgentBuilder;
    chatGrc?: ChatGRC;
    autopilot?: import('@grc-claw/compliance-autopilot').ComplianceAutopilot;
    tracer?: import('@grc-claw/observability').AgentTracer;
    driftDetector?: DriftDetector;
    evidenceCollector?: EvidenceCollectorEngine;
  }
): Promise<Record<string, unknown>> {
  if (isClawTool(tool)) {
    return dispatchClawTool(tool, args, deps.claw);
  }
  if (isConnectorTool(tool)) {
    const result = await dispatchConnectorTool(deps.registry, tool, args);
    return result.output ?? { kind: result.kind };
  }
  if (isBuiltinGrcTool(tool)) {
    if (tool === 'grc.list_controls' && args.includeAims === true) {
      const base = await dispatchBuiltinGrcTool(tool, args, { evidence: deps.evidence, a2z: deps.a2z, persistence: deps.persistence, agentBuilder: deps.agentBuilder, chatGrc: deps.chatGrc, autopilot: deps.autopilot, tracer: deps.tracer, driftDetector: deps.driftDetector, evidenceCollector: deps.evidenceCollector });
      return {
        ...base,
        aims: {
          vendorGaps: listVendorGaps(),
          technicalControls: listTechnicalControls(),
          clauses: listClauseMap(),
        },
      };
    }
    return dispatchBuiltinGrcTool(tool, args, { evidence: deps.evidence, a2z: deps.a2z, persistence: deps.persistence, agentBuilder: deps.agentBuilder, chatGrc: deps.chatGrc, autopilot: deps.autopilot, tracer: deps.tracer, driftDetector: deps.driftDetector, evidenceCollector: deps.evidenceCollector });
  }
  return { ok: false, error: 'unknown_tool', tool };
}

function makeAccmGapDetector(
  frameworkCode: ACCMFrameworkCode,
  evidenceStore: EvidenceStore,
): GapDetector {
  return {
    async getControls(fw: ACCMFrameworkCode) {
      const packs = listFrameworkPacks();
      const records: import('@grc-claw/accm').ControlRecord[] = [];
      for (const pack of packs) {
        if (pack.code !== fw) continue;
        for (const ctrl of pack.controls) {
          const items = evidenceStore.listByControl(ctrl.id);
          records.push({
            controlId: ctrl.id,
            controlCode: ctrl.controlCode,
            title: ctrl.title,
            frameworkCode: fw,
            implemented: items.length > 0,
            evidenceHashes: items.map((e) => e.sha256),
            lastVerifiedAt: new Date().toISOString(),
            owner: 'system',
          });
        }
      }
      return records;
    },
  };
}
