import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { timingSafeEqual } from 'node:crypto';
import { join } from 'node:path';
import { WebSocketServer, type WebSocket } from 'ws';
import { A2ZSocConnector, loadA2ZConfigFromEnv } from '@grc-claw/a2z-connector';
import { AgentSession, BUILTIN_AGENT_TOOLS, type ExecPolicy, PersistentMemoryStore, type ToolTier } from '@grc-claw/agent-runtime';
import { getConnectorRegistry, isConnectorTool } from '@grc-claw/connectors';
import { ActionLedger, createAssuranceEnvelope, EvidenceStore, type ActionLedgerEvent } from '@grc-claw/evidence';
import { buildEvidenceGraphSnapshot as buildEvidenceGraphObjectSnapshot, edgeObject, nodeObject } from '@grc-claw/evidence-graph';
import {
  AIMS_SCOPE_TEMPLATE,
  listClauseMap,
  listTechnicalControls,
  listVendorGapSummary,
  listVendorGaps,
  type VendorId,
} from '@grc-claw/aims';
import { listFrameworkPacks } from '@grc-claw/frameworks';
import { CLOUD_INGEST_SOURCES, normalizeBySource, type IngestSource } from '@grc-claw/ingest';
import {
  buildExecPolicyWithConnectors,
  handleConnectorsRoute,
} from './connectors-api.js';
import { IdempotencyCache } from './idempotency.js';
import { applyCors, tryServeConsoleStatic } from './console-static.js';
import { discoverCursorSkills } from './cursor-skills.js';
import { dispatchAgentTool, executionStateFromOutput, setSecurityGraph, identityManager, agentAuditTrail } from './agent-dispatch.js';
import { createClawDispatchContext } from './skill-runtime.js';
import { GatewayAssuranceGraph } from './assurance.js';
import { initSecurityGraph } from './graph-init.js';
import { getSkillById, listSkills } from '@grc-claw/skill-executor';
import { createRateLimiter } from './rate-limiter.js';
import { applySecurityHeaders } from './security-headers.js';
import { metricsCollector } from './metrics.js';
import { initPersistence, getPersistence, isPersistenceEnabled, closePersistence } from './persistence-init.js';
import type { PersistenceLayer } from '@grc-claw/persistence';
import { MonteCarloEngine, FAIRCalculator, RiskRegister } from '@grc-claw/risk-quantification';
import { EntityManager } from '@grc-claw/entity-management';
import { ACCMEngine, type FrameworkCode as ACCMFrameworkCode, type ControlRecord as ACCMControlRecord, type GapDetector } from '@grc-claw/accm';
import { AgentBuilder, PREBUILT_AGENTS, type AgentDefinition } from '@grc-claw/agent-builder';
import { FrameworkCrosswalk } from '@grc-claw/framework-crosswalk';
import { ChatGRC } from '@grc-claw/chat-grc';
import { BoardReportGenerator } from '@grc-claw/board-reporting';
import { VendorRegistry } from '@grc-claw/third-party-risk';
import { QuestionnaireAutomation, QuestionnaireAnswerEngine } from '@grc-claw/questionnaire-automation';
import { ComplianceProver } from '@grc-claw/zk-compliance';
import { AgentTracer } from '@grc-claw/observability';
import { ComplianceAutopilot } from '@grc-claw/compliance-autopilot';
import { DriftDetector, type ControlEvaluator, type ControlSnapshot } from '@grc-claw/drift-detector';
import { EvidenceCollectorEngine, type SystemAdapter, type ComplianceFramework as ECFramework } from '@grc-claw/evidence-collector';
import { IntegrationMarketplace } from '@grc-claw/integration-marketplace';
import { PolicyManagementHub } from '@grc-claw/policy-management-hub';
import { VendorRiskManagement } from '@grc-claw/vendor-risk-management';
import { EmployeeLifecycleEngine } from '@grc-claw/employee-lifecycle';
import { ComplianceTaskEngine } from '@grc-claw/compliance-task-engine';
import { EvidenceAutomationEngine } from '@grc-claw/evidence-automation-engine';
import { OpenAPIGenerator } from '@grc-claw/openapi-generator';
import { AgentDiscoveryScanner } from '@grc-claw/agent-discovery';
import { RBACEngine, type JWTPayload } from '@grc-claw/rbac-multi-tenant';
import { TerraformProvider } from '@grc-claw/terraform-provider';
import { ContinuousTrustEngine } from '@grc-claw/continuous-trust-engine';
import { AgentCollaboration } from '@grc-claw/agent-collaboration';
import { RegulatoryChangeManagement } from '@grc-claw/regulatory-change-management';
import { AIGovernance } from '@grc-claw/ai-governance';
import { ComplianceKnowledgeGraph } from '@grc-claw/compliance-knowledge-graph';
import { PredictiveComplianceEngine } from '@grc-claw/predictive-compliance';
import { ComplianceMarketplace } from '@grc-claw/compliance-marketplace';
import { ZeroTrustAuditTrail } from '@grc-claw/zero-trust-audit';
import { FederatedLearningNetwork } from '@grc-claw/federated-learning';
import { ComplianceIntelligenceAPI } from '@grc-claw/compliance-intelligence-api';
import { AutonomousComplianceAgent } from '@grc-claw/autonomous-compliance-agent';
import { ComplianceDigitalTwin } from '@grc-claw/compliance-digital-twin';
import { QuantumResistantCrypto } from '@grc-claw/quantum-resistant-crypto';
import { NaturalLanguageCompliance } from '@grc-claw/natural-language-compliance';
import { ComplianceAutomationMarketplace } from '@grc-claw/compliance-automation-marketplace';
import { RealTimeComplianceMonitor } from '@grc-claw/real-time-compliance-monitor';

const REQUEST_TIMEOUT_MS = 30_000;
const MAX_BODY_BYTES = 1 * 1024 * 1024;

export interface TenantContext {
  userId?: string;
  tenantId?: string;
  role?: string;
  scope?: string;
  permissions?: string[];
  jwtPayload?: JWTPayload;
}

export interface GatewayRequest extends IncomingMessage {
  tenantContext?: TenantContext;
}

// SOC event broadcaster — pushes normalized events to all subscribed WS clients
const socClients = new Set<WebSocket>();

// Compliance update broadcaster — pushes real-time compliance posture changes
const complianceClients = new Set<WebSocket>();

function broadcastSocEvent(event: unknown): void {
  const msg = JSON.stringify({ type: 'soc_event', data: event, ts: new Date().toISOString() });
  for (const client of socClients) {
    try {
      if (client.readyState === 1 /* OPEN */) {
        client.send(msg);
      } else {
        socClients.delete(client);
      }
    } catch {
      socClients.delete(client);
    }
  }
}

function broadcastComplianceUpdate(compliance: Record<string, unknown>): void {
  const msg = JSON.stringify({ type: 'compliance_update', data: compliance, ts: new Date().toISOString() });
  for (const client of complianceClients) {
    try {
      if (client.readyState === 1 /* OPEN */) {
        client.send(msg);
      } else {
        complianceClients.delete(client);
      }
    } catch {
      complianceClients.delete(client);
    }
  }
}

export interface GatewayConfig {
  host: string;
  port: number;
  token: string;
}

export function createGateway(config: GatewayConfig, persistence?: PersistenceLayer | null) {
  const seededGraph = initSecurityGraph();
  setSecurityGraph(seededGraph);

  const tracer = new AgentTracer({
    serviceName: 'grc-claw-gateway',
    version: '1.0.0',
    environment: process.env.NODE_ENV ?? 'development',
  });

  const dedupe = new IdempotencyCache();
  const pg = persistence ?? getPersistence();
  const evidence = new EvidenceStore(pg?.database);
  const ledger = new ActionLedger(
    process.env.GRC_CLAW_ACTION_LEDGER_PATH?.trim() || join(process.cwd(), '.grc_memory', 'action-ledger.ndjson')
  );
  const assurance = new GatewayAssuranceGraph();
  const a2z = new A2ZSocConnector(loadA2ZConfigFromEnv());
  const connectors = getConnectorRegistry();
  const store = new PersistentMemoryStore(process.env.GRC_CLAW_MEMORY_DIR?.trim() || '.grc_memory');
  const rateLimiter = createRateLimiter();
  const riskRegister = new RiskRegister();
  const entityManager = new EntityManager(pg?.database);
  const agentBuilder = new AgentBuilder(pg?.database ? { database: pg.database } : undefined);
  const frameworkCrosswalk = new FrameworkCrosswalk();
  const chatGRC = new ChatGRC();

  // ─── RBAC Engine (multi-tenant auth) ─────────────────────────────────
  const rbacEngine = new RBACEngine({
    jwtSecret: process.env.GRC_CLAW_JWT_SECRET?.trim() || config.token,
    jwtExpiresIn: Number(process.env.GRC_CLAW_JWT_EXPIRES_IN ?? 3600),
    auditLogLimit: 10000,
  });

  // Create a default tenant for backward compatibility
  const defaultTenant = rbacEngine.createTenant('default');

  // ─── Terraform Provider (IaC for GRC resources) ─────────────────────
  const terraformProvider = new TerraformProvider();

  // Load persisted data from database into in-memory stores on startup
  if (pg?.database) {
    evidence.loadFromDatabase().catch((err) => {
      console.warn('[STARTUP] evidence.loadFromDatabase failed:', err instanceof Error ? err.message : err);
    });
    entityManager.loadFromDatabase().catch((err) => {
      console.warn('[STARTUP] entityManager.loadFromDatabase failed:', err instanceof Error ? err.message : err);
    });
    agentBuilder.initializeStore().catch((err) => {
      console.warn('[STARTUP] agentBuilder.initializeStore failed:', err instanceof Error ? err.message : err);
    });
    identityManager.setDatabase(pg.database);
    identityManager.initializeDatabase().catch((err) => {
      console.warn('[STARTUP] identityManager.initializeDatabase failed:', err instanceof Error ? err.message : err);
    });
    identityManager.loadFromDatabase().catch((err) => {
      console.warn('[STARTUP] identityManager.loadFromDatabase failed:', err instanceof Error ? err.message : err);
    });
  }

  // ACCM GapDetector: bridges framework packs + evidence store to ACCMEngine
  const accmGapDetector: GapDetector = {
    async getControls(frameworkCode: ACCMFrameworkCode): Promise<ACCMControlRecord[]> {
      const packs = listFrameworkPacks();
      const records: ACCMControlRecord[] = [];
      for (const pack of packs) {
        if (pack.code !== frameworkCode) continue;
        for (const ctrl of pack.controls) {
          const evidenceItems = evidence.listByControl(ctrl.id);
          records.push({
            controlId: ctrl.id,
            controlCode: ctrl.controlCode,
            title: ctrl.title,
            frameworkCode: frameworkCode as ACCMFrameworkCode,
            implemented: evidenceItems.length > 0,
            evidenceHashes: evidenceItems.map((e) => e.sha256),
            lastVerifiedAt: new Date().toISOString(),
            owner: 'system',
          });
        }
      }
      return records;
    },
  };
  const accmEngine = new ACCMEngine(accmGapDetector, { tenantId: 'default', autoRemediate: true });
  const boardReporter = new BoardReportGenerator();
  const vendorRegistry = new VendorRegistry();
  const questionnaireAutomation = new QuestionnaireAutomation();
  const questionnaireAnswerEngine = new QuestionnaireAnswerEngine();
  const complianceProver = new ComplianceProver();
  const autopilot = new ComplianceAutopilot({
    frameworks: ['iso27001', 'soc2', 'nist_csf', 'cis_controls'],
    evidenceDb: pg?.database,
    autoRemediate: true,
    tenantId: 1,
  });
  const integrationMarketplace = new IntegrationMarketplace();
  const policyHub = new PolicyManagementHub();
  const vendorRiskMgmt = new VendorRiskManagement();
  const employeeLifecycle = new EmployeeLifecycleEngine();
  const complianceTaskEngine = new ComplianceTaskEngine();
  const evidenceAutoEngine = new EvidenceAutomationEngine();

  // --- New Enterprise Services ---
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
  const buildEvidenceGraphSnapshot = (organizationId = 'demo-org') => {
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
        source: 'gateway',
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
        source: 'gateway',
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
  };

  // ─── Drift Detector ─────────────────────────────────────────────────
  const driftControlEvaluator: ControlEvaluator = {
    async listControls(framework: string): Promise<Array<{ controlId: string; title: string }>> {
      const packs = listFrameworkPacks();
      const results: Array<{ controlId: string; title: string }> = [];
      for (const pack of packs) {
        if (pack.code !== framework) continue;
        for (const ctrl of pack.controls) {
          results.push({ controlId: ctrl.id, title: ctrl.title });
        }
      }
      return results;
    },
    async evaluateControl(controlId: string, framework: string): Promise<ControlSnapshot> {
      let items: Array<{ sha256: string }> = [];
      if (pg) {
        try { items = await evidence.listByControlFromDb(controlId); } catch { items = evidence.listByControl(controlId); }
      } else {
        items = evidence.listByControl(controlId);
      }
      const status = items.length > 0 ? 'compliant' as const : 'unknown' as const;
      return {
        controlId,
        framework,
        status,
        evidenceHashes: items.map((e) => e.sha256),
        evidenceCount: items.length,
        complianceScore: items.length > 0 ? 1 : 0,
        lastCheckedAt: new Date().toISOString(),
      };
    },
  };

  const driftDetector = new DriftDetector(
    {
      tenantId: 1,
      frameworks: listFrameworkPacks().map((p) => p.code),
      driftThresholdPercent: 5,
      scoreDeltaAlertThreshold: 10,
      pollIntervalMs: 300_000,
      onDrift: (events) => {
        broadcastComplianceUpdate({
          overall_score: 0,
          frameworks: {},
          trigger: 'drift_detected',
          driftEvents: events.map((e) => ({ controlId: e.controlId, severity: e.severity, description: e.description })),
        });
      },
    },
    driftControlEvaluator,
  );

  // ─── Evidence Collector ──────────────────────────────────────────────
  function deterministicHash(input: string): number {
    let h = 0;
    for (let i = 0; i < input.length; i++) {
      h = (h << 5) - h + input.charCodeAt(i);
      h = h & h;
    }
    return Math.abs(h);
  }
  const pgSystemAdapter: SystemAdapter = {
    async queryMFA() {
      if (pg) {
        try {
          const { rows } = await pg.database.query(
            "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE metadata->>'mfa_enabled' = 'true') AS mfa_enabled FROM users WHERE tenant_id = $1",
            [String(1)],
          );
          const total = Number(rows[0]?.total ?? 0);
          const mfaEnabled = Number(rows[0]?.mfa_enabled ?? 0);
          return { enforced: mfaEnabled === total && total > 0, totalUsers: total, mfaEnabledUsers: mfaEnabled, methods: ['totp'] };
        } catch { /* fall through */ }
      }
      return { enforced: false, totalUsers: 0, mfaEnabledUsers: 0, methods: [] };
    },
    async queryEncryptionAtRest() {
      const h = deterministicHash('encryption-at-rest');
      const enabled = h % 10 !== 0;
      const algorithms = ['AES-256', 'AES-128', 'ChaCha20-Poly1305'];
      const algorithm = algorithms[h % algorithms.length];
      const keyRotationDays = [30, 60, 90][h % 3];
      return { enabled, algorithm, keyRotationDays, details: { source: 'gateway_hash_based', tenantHash: h % 100 } };
    },
    async queryEncryptionInTransit() {
      return { enabled: true, algorithm: 'TLS-1.3', details: { source: 'gateway_default' } };
    },
    async queryAccessControl() {
      if (pg) {
        try {
          const { rows } = await pg.database.query(
            "SELECT COUNT(DISTINCT role) AS roles FROM user_roles WHERE tenant_id = $1",
            [String(1)],
          );
          return { leastPrivilege: true, totalRoles: Number(rows[0]?.roles ?? 0), excessiveRoles: 0, details: {} };
        } catch { /* fall through */ }
      }
      return { leastPrivilege: true, totalRoles: 0, excessiveRoles: 0, details: {} };
    },
    async queryLogging() {
      return { enabled: true, logTypes: ['audit', 'access', 'error'], retentionDays: 90, alertingEnabled: true, details: {} };
    },
    async queryPatchManagement() {
      const h = deterministicHash('patch-management');
      const pendingPatches = h % 15;
      const criticalPatches = h % 4;
      const autoUpdateEnabled = h % 5 !== 0;
      const daysAgo = h % 30;
      const lastPatch = new Date(Date.now() - daysAgo * 86400000).toISOString();
      return { lastPatchDate: lastPatch, pendingPatches, criticalPatches, autoUpdateEnabled, details: { tenantHash: h % 100 } };
    },
    async queryNetworkSecurity() {
      const h = deterministicHash('network-security');
      const firewallEnabled = h % 10 !== 0;
      const segmentationEnabled = h % 7 !== 0;
      const totalRules = 5 + (h % 50);
      const openPorts = h % 12;
      return { firewallEnabled, segmentationEnabled, totalRules, openPorts, details: { tenantHash: h % 100 } };
    },
    async queryBackup() {
      const h = deterministicHash('backup-status');
      const frequencies = ['daily', 'hourly', 'weekly'];
      const frequency = frequencies[h % frequencies.length];
      const retentionDays = [14, 30, 60, 90][h % 4];
      const testPassed = h % 4 !== 0;
      return { configured: true, frequency, retentionDays, testPassed, details: { tenantHash: h % 100 } };
    },
  };
  const evidenceCollector = new EvidenceCollectorEngine(pgSystemAdapter);

  let execPolicy!: ExecPolicy;

  async function persistAssuranceEnvelope(
    intent: ActionLedgerEvent,
    decision: ActionLedgerEvent,
    result: ActionLedgerEvent | undefined,
    snapshot: ReturnType<GatewayAssuranceGraph['get']>
  ): Promise<{ envelopeId?: string; actionId: string; executionState: 'recorded' | 'not_configured' | 'failed' }> {
    const envelope = createAssuranceEnvelope({
      intent,
      decision,
      result,
      identity: snapshot ? { agentDid: snapshot.agentDid, status: snapshot.identityStatus } : undefined,
      assurance: snapshot
        ? {
            riskScore: snapshot.risk.overallRisk,
            blastRadiusImpact: snapshot.blastRadius?.impactScore,
            controlId: snapshot.blastRadius?.controlId,
          }
        : undefined,
    });
    try {
      return await a2z.recordAssuranceEnvelope(
        intent.tenantId,
        envelope,
        `assurance-${intent.actionId}`
      );
    } catch {
      return { actionId: intent.actionId, executionState: 'failed' };
    }
  }

  async function refreshExecPolicy(): Promise<ExecPolicy> {
    execPolicy = await buildExecPolicyWithConnectors(connectors);
    return execPolicy;
  }

  void refreshExecPolicy();

  function makeClawContext(policy: ExecPolicy) {
    const llmProviders = connectors.listLlm();
    return createClawDispatchContext({
      registry: connectors,
      evidence,
      ledger,
      a2z,
      defaultLlmProviderId: llmProviders[0]?.id ?? 'gemini',
      getPolicy: () => policy,
      makeSession: (sessionId, pol) => new AgentSession(sessionId, pol, store),
    });
  }

  function authOk(req: IncomingMessage): boolean {
    const header = req.headers['x-grc-claw-token'] ?? req.headers.authorization;
    const rawToken =
      typeof header === 'string' && header.startsWith('Bearer ')
        ? header.slice(7)
        : String(header ?? '');

    // Attempt RBAC JWT verification first
    if (rawToken.split('.').length === 3) {
      const jwtPayload = rbacEngine.verifyJWT(rawToken);
      if (jwtPayload) {
        const gwReq = req as GatewayRequest;
        gwReq.tenantContext = {
          userId: jwtPayload.sub,
          tenantId: jwtPayload.tenant_id,
          role: jwtPayload.role,
          scope: jwtPayload.scope,
          permissions: jwtPayload.permissions,
          jwtPayload,
        };
        return true;
      }
    }

    // Fallback: simple token auth (backward compatibility)
    const secretBuf = Buffer.from(config.token, 'utf8');
    const tokenBuf = Buffer.from(rawToken, 'utf8');

    if (secretBuf.length !== tokenBuf.length) {
      logAuthFailure(req, 'length_mismatch');
      return false;
    }

    const match = timingSafeEqual(secretBuf, tokenBuf);
    if (match) {
      // Simple token auth — assign default tenant context
      const gwReq = req as GatewayRequest;
      gwReq.tenantContext = {
        userId: 'token-auth',
        tenantId: defaultTenant.id,
        role: 'admin',
        scope: 'global',
        permissions: ['*'],
      };
    } else {
      logAuthFailure(req, 'token_mismatch');
    }
    return match;
  }

  function logAuthFailure(req: IncomingMessage, reason: string): void {
    const ip = req.headers['x-forwarded-for'] ?? req.socket.remoteAddress ?? 'unknown';
    const endpoint = req.url ?? '/';
    console.warn(
      `[SECURITY] auth_failure ip=${ip} reason=${reason} endpoint=${endpoint} timestamp=${new Date().toISOString()}`
    );
  }

  const httpServer = createServer(async (req, res) => {
    applySecurityHeaders(res);
    applyCors(res);

    const requestStart = Date.now();
    metricsCollector.incCounter('grc_gateway_requests_total');

    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      try {
        if (!res.headersSent) {
          res.writeHead(508, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'request_timeout' }));
        }
      } catch {}
    }, REQUEST_TIMEOUT_MS);
    const clearTimer = () => {
      clearTimeout(timeout);
      const duration = Date.now() - requestStart;
      metricsCollector.observeHistogram('grc_request_duration_ms', duration);
    };
    res.on('finish', clearTimer);
    res.on('close', clearTimer);

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    if (timedOut) return;

    if (!rateLimiter.middleware(req, res, req.method ?? 'GET')) return;

    if (timedOut) return;

    const path = req.url?.split('?')[0] ?? '/';

    if (path === '/metrics' && req.method === 'GET') {
      const packs = listFrameworkPacks();
      let totalControls = 0;
      let controlsWithEvidence = 0;
      for (const pack of packs) {
        for (const ctrl of pack.controls) {
          totalControls++;
          if (pg) {
            try {
              const items = await evidence.listByControlFromDb(ctrl.id);
              if (items.length > 0) controlsWithEvidence++;
            } catch {
              if (evidence.listByControl(ctrl.id).length > 0) controlsWithEvidence++;
            }
          } else {
            if (evidence.listByControl(ctrl.id).length > 0) controlsWithEvidence++;
          }
        }
      }
      const realScore = totalControls > 0 ? controlsWithEvidence / totalControls : 0;
      metricsCollector.setGauge('grc_compliance_score', Math.round(realScore * 100) / 100);
      const metricsText = metricsCollector.getPrometheusFormat();
      res.writeHead(200, { 'Content-Type': 'text/plain; version=0.0.4; charset=utf-8' });
      res.end(metricsText);
      return;
    }

    if (path === '/health') {
      const summary = connectors.toPublicSummary();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: true,
          service: 'grc-claw-gateway',
          a2z_soc_mode: process.env.A2Z_SOC_MODE ?? 'demo',
          agentic_ai_security: true,
          cloud_security_integration: true,
          iso_42001_aims: true,
          byoc_connectors: true,
          llm_providers: summary.llm.length,
          mcp_servers: summary.mcp.length,
          cloud_sources: CLOUD_INGEST_SOURCES,
          persistence: isPersistenceEnabled() ? 'postgresql' : 'demo',
          soc_stream: 'ws://host/ws — subscribe with {"type":"subscribe","channel":"soc_events","token":"<token>"} to receive real-time normalized SOC events',
          marketing: 'The OSS chassis for ISO 42001-compliant agentic AI — pairs with a2zsoc.com',
        })
      );
      return;
    }

    if (path === '/api/db/health') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      if (!pg) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, mode: 'demo', postgresql: false, message: 'No DATABASE_URL — running in demo mode' }));
        return;
      }
      try {
        const healthy = await pg.database.healthCheck();
        res.writeHead(healthy ? 200 : 503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: healthy, mode: 'production', postgresql: true }));
      } catch {
        res.writeHead(503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, mode: 'production', postgresql: true, error: 'health_check_failed' }));
      }
      return;
    }

    const connectorHandled = await handleConnectorsRoute(
      req,
      res,
      path,
      authOk,
      readJson,
      async () => execPolicy ?? refreshExecPolicy(),
      async () => {
        await refreshExecPolicy();
      },
      ledger
    );
    if (connectorHandled) return;

    if (path === '/api/action-ledger' && req.method === 'GET') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      const limit = Number(new URL(req.url ?? '', 'http://local').searchParams.get('limit') ?? 100);
      let events: unknown[] = ledger.list(limit);
      let source = 'in-memory';
      if (pg) {
        try {
          const { rows } = await pg.database.query(
            'SELECT * FROM action_ledger ORDER BY created_at DESC LIMIT $1',
            [limit]
          );
          if (rows.length > 0) {
            events = rows;
            source = 'postgresql';
          }
        } catch {
          // fall back to in-memory
        }
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, source, events, integrity: ledger.verify() }));
      return;
    }

    if (path === '/api/assurance' && req.method === 'GET') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...assurance.summary() }));
      return;
    }

    if (path === '/api/frameworks' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ packs: listFrameworkPacks() }));
      return;
    }

    if (path === '/api/cursor-skills' && req.method === 'GET') {
      const skills = discoverCursorSkills();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: true,
          note: 'Skill catalog — execute via claw.list_skills, claw.get_skill, claw.run_skill or POST /api/skills/run',
          skills,
        })
      );
      return;
    }

    if (path === '/api/skills' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, skills: listSkills() }));
      return;
    }

    const skillDetail = path.match(/^\/api\/skills\/([^/]+)$/);
    if (skillDetail && req.method === 'GET') {
      const skillId = decodeURIComponent(skillDetail[1]!);
      const includeBody = new URL(req.url ?? '', 'http://local').searchParams.get('body') !== '0';
      const skill = getSkillById(skillId);
      if (!skill) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: 'skill_not_found', skillId }));
        return;
      }
      if (!includeBody) {
        const { body: _b, ...meta } = skill;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, skill: { ...meta, hasBody: true } }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, skill }));
      return;
    }

    if (path === '/api/skills/run' && req.method === 'POST') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      let body: Record<string, unknown>;
      try {
        body = await readJson(req);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'invalid_body';
        const status = msg === 'request_body_too_large' ? 413 : 400;
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
        return;
      }
      const validation = validateBody(body, ['skillId', 'task']);
      if (!validation.valid) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'missing_required_field', field: validation.missing }));
        return;
      }
      const skillId = String(body.skillId ?? '');
      const task = String(body.task ?? '');
      const policy = execPolicy ?? (await refreshExecPolicy());
      const session = new AgentSession(String(body.sessionId ?? 'skill-run'), policy, store);
      const idem = String(body.idempotencyKey ?? `skill-run-${skillId}-${Date.now()}`);
      const decision = await session.invoke({
        tool: 'claw.run_skill',
        args: body,
        idempotencyKey: idem,
      });
      if (!decision.allowed) {
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, decision, audit: session.getAuditLog() }));
        return;
      }
      const skillTrace = tracer.startTrace(`skill.${skillId}`, {
        'tool.name': skillId,
        'agent.session_id': session.sessionId,
        'tool.tier': 'read',
        'policy.result': 'allow',
      });
      const claw = makeClawContext(policy);
      let result: Awaited<ReturnType<typeof claw.runSkill>>;
      try {
        result = await claw.runSkill({
          skillId,
          task,
          llmProviderId: typeof body.llmProviderId === 'string' ? body.llmProviderId : undefined,
          maxSteps: typeof body.maxSteps === 'number' ? body.maxSteps : undefined,
          readOnlyTools: body.readOnlyTools !== false,
        });
        tracer.endSpan(skillTrace.spanId, result.ok ? 'OK' : 'ERROR');
      } catch (e) {
        tracer.endSpan(skillTrace.spanId, 'ERROR', e instanceof Error ? e.message : 'skill_failed');
        throw e;
      }
      metricsCollector.incCounter('grc_agent_invocations_total');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: result.ok,
          decision,
          result,
          audit: session.getAuditLog(),
        })
      );
      return;
    }

    if (path === '/api/aims/vendor-gaps' && req.method === 'GET') {
      const vendor = new URL(req.url ?? '', 'http://local').searchParams.get('vendor') as VendorId | null;
      const valid = vendor && ['anthropic', 'openai', 'cursor', 'openclaw'].includes(vendor);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          summary: listVendorGapSummary(),
          gaps: listVendorGaps(valid ? vendor : undefined),
        })
      );
      return;
    }

    if (path === '/api/aims/technical-controls' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          scope: AIMS_SCOPE_TEMPLATE,
          clauses: listClauseMap(),
          controls: listTechnicalControls(),
        })
      );
      return;
    }

    if (path === '/api/ingest/normalize' && req.method === 'POST') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      let body: Record<string, unknown>;
      try {
        body = await readJson(req);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'invalid_body';
        const status = msg === 'request_body_too_large' ? 413 : 400;
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
        return;
      }
      const validation = validateBody(body, ['source']);
      if (!validation.valid) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'missing_required_field', field: validation.missing }));
        return;
      }
      const source = String(body.source ?? '') as IngestSource;
      const tenantId = Number(body.tenantId ?? 1);
      const payload = body.payload;
      const ingestSpan = tracer.startTrace(`ingest.normalize.${source}`, {
        'tool.name': `ingest.${source}`,
        'agent.tenant_id': String(tenantId),
        'policy.result': 'allow',
      });
      const event = normalizeBySource(source, payload, tenantId);
      if (!event) {
        tracer.endSpan(ingestSpan.spanId, 'ERROR', 'normalize_failed');
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'normalize_failed', source }));
        return;
      }
      tracer.setAttributes(ingestSpan.spanId, { 'evidence.type': event.eventType });
      // Broadcast normalized event to all subscribed SOC WebSocket clients
      broadcastSocEvent(event);
      const impact = await a2z.mapSecurityEventToControls({
        eventUuid: event.eventUuid,
        eventType: event.eventType,
        severity: event.severity,
        sourceSystem: event.sourceSystem,
        tenantId: event.tenantId,
        eventData: event.eventData,
      });
      tracer.endSpan(ingestSpan.spanId, 'OK');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, event, complianceImpact: impact }));
      return;
    }

    if (path === '/api/a2z/sync' && req.method === 'POST') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      const since = new Date(Date.now() - 3600_000).toISOString();
      const result = await a2z.syncInbound(since);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...result, source: 'Private A2Z SOC bridge' }));
      return;
    }

    if (path === '/api/agent/invoke' && req.method === 'POST') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      let body: Record<string, unknown>;
      try {
        body = await readJson(req);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'invalid_body';
        const status = msg === 'request_body_too_large' ? 413 : 400;
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
        return;
      }
      const validation = validateBody(body, ['tool']);
      if (!validation.valid) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'missing_required_field', field: validation.missing }));
        return;
      }
      const idem = String(body.idempotencyKey ?? '');
      if (idem && dedupe.seen(idem)) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, deduped: true }));
        return;
      }
      const policy = execPolicy ?? (await refreshExecPolicy());
      const session = new AgentSession(String(body.sessionId ?? 'default'), policy, store);
      const sessionId = session.sessionId;
      const tool = String(body.tool ?? '');
      const args = (body.args as Record<string, unknown>) ?? {};
      const intent = ledger.recordIntent({
        tenantId: Number(args.tenantId ?? body.tenantId ?? 1),
        sessionId,
        tool,
        args,
        idempotencyKey: idem || undefined,
      });
      const assuranceSnapshot = await assurance.observeIntent(intent, {
        agentId: typeof body.agentId === 'string' ? body.agentId : undefined,
        tenantId: intent.tenantId,
        sessionId,
        tool,
        args,
        toolTier: toolTierFor(tool),
      });
      if (!assuranceSnapshot.gate.allowed) {
        const decision = {
          allowed: false,
          reason: assuranceSnapshot.gate.reason ?? 'assurance_denied',
          sandbox: 'denied' as const,
          requiresApproval: true,
        };
        const decisionEvent = ledger.recordDecision(intent, decision);
        const updatedAssurance = assurance.observeDecision(intent, false, decision.reason);
        const assuranceReceipt = await persistAssuranceEnvelope(intent, decisionEvent, undefined, updatedAssurance);
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ decision, assurance: updatedAssurance, assuranceReceipt, action: { id: intent.actionId, executionState: 'approval_required' }, audit: session.getAuditLog() }));
        return;
      }
      const decision = await session.invoke({
        tool,
        args,
        approvalToken: body.approvalToken as string | undefined,
        idempotencyKey: idem || undefined,
      });
      const decisionEvent = ledger.recordDecision(intent, decision);
      const updatedAssurance = assurance.observeDecision(intent, decision.allowed, decision.reason);
      if (!decision.allowed) {
        const assuranceReceipt = await persistAssuranceEnvelope(intent, decisionEvent, undefined, updatedAssurance);
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ decision, assurance: updatedAssurance, assuranceReceipt, action: { id: intent.actionId, executionState: decision.requiresApproval ? 'approval_required' : 'denied' }, audit: session.getAuditLog() }));
        return;
      }
      let output: Record<string, unknown> | undefined;
      const traceSpan = tracer.startTrace(`agent.tool.${tool}`, {
        'agent.did': typeof body.agentId === 'string' ? body.agentId : 'system',
        'agent.session_id': sessionId,
        'tool.name': tool,
        'tool.tier': toolTierFor(tool),
        'policy.result': decision.allowed ? 'allow' : 'deny',
      });
      try {
        const claw = makeClawContext(policy);
        output = await dispatchAgentTool(tool, args, {
          registry: connectors,
          evidence,
          a2z,
          claw,
          persistence: pg,
          agentBuilder,
          chatGrc: chatGRC,
          tracer,
          driftDetector,
          evidenceCollector,
        });
        tracer.endSpan(traceSpan.spanId, 'OK');
        metricsCollector.incCounter('grc_agent_invocations_total');
        agentAuditTrail.record(
          typeof body.agentId === 'string' ? body.agentId : 'system',
          tool,
          args,
          output ?? {},
        );
      } catch (e) {
        tracer.endSpan(traceSpan.spanId, 'ERROR', e instanceof Error ? e.message : 'dispatch_failed');
        const resultEvent = ledger.recordResult(intent, { executionState: 'failed' });
        const assuranceReceipt = await persistAssuranceEnvelope(intent, decisionEvent, resultEvent, assurance.get(intent.actionId));
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            decision,
            error: e instanceof Error ? e.message : 'agent_dispatch_failed',
            assurance: assurance.get(intent.actionId),
            assuranceReceipt,
            audit: session.getAuditLog(),
          })
        );
        return;
      }
      const executionState = executionStateFromOutput(output);
      const action = ledger.recordResult(intent, {
        executionState,
        output,
        evidenceId:
          typeof output.evidence === 'object' && output.evidence && 'id' in output.evidence
            ? String((output.evidence as { id: unknown }).id)
            : undefined,
        targetReceipt: typeof output.targetReceipt === 'string' ? output.targetReceipt : undefined,
      });
      const assuranceReceipt = await persistAssuranceEnvelope(intent, decisionEvent, action, assurance.get(intent.actionId));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: executionState !== 'failed' && executionState !== 'not_configured',
          decision,
          output,
          action: { id: action.actionId, executionState },
          assurance: assurance.get(intent.actionId),
          assuranceReceipt,
          audit: session.getAuditLog(),
        })
      );
      return;
    }

    // --- Risk Quantification Endpoints ---
    if (req.method === 'POST' && path === '/api/risk/monte-carlo') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const engine = new MonteCarloEngine(body.scenario as unknown as import('@grc-claw/risk-quantification').RiskScenario, { iterations: body.iterations as number, seed: body.seed as number });
        const result = engine.run();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/risk/fair') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const calc = new FAIRCalculator(body.scenario as unknown as import('@grc-claw/risk-quantification').RiskScenario, { iterations: body.iterations as number, seed: body.seed as number });
        const result = calc.calculate();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/risk/register') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const entries = riskRegister.getAllEntries();
      const metrics = riskRegister.portfolioMetrics();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, entries, metrics }));
      return;
    }
    if (req.method === 'POST' && path === '/api/risk/scenarios') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const entry = riskRegister.addScenario(body as unknown as import('@grc-claw/risk-quantification').RiskScenario);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, entry }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/risk/heatmap') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const heatmap = riskRegister.generateHeatMap(5);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...heatmap }));
      return;
    }

    // --- Entity Management Endpoints ---
    if (req.method === 'POST' && path === '/api/entities') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const entity = entityManager.createEntity(body as Parameters<typeof entityManager.createEntity>[0]);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, entity }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && /^\/api\/entities\/?$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const entities = entityManager.listEntities();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, entities }));
      return;
    }
    if (req.method === 'GET' && /^\/api\/entities\/[^/]+$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = path.split('/').pop()!;
      const entity = entityManager.getEntity(id);
      if (!entity) { res.writeHead(404); res.end(JSON.stringify({ error: 'not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, entity }));
      return;
    }
    if (req.method === 'POST' && /^\/api\/entities\/[^/]+\/relationships$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const entityId = path.split('/')[3];
        const body = await readJson(req);
        const rel = entityManager.addRelationship(entityId, body.childEntityId as string, body.relationshipType as 'ownership' | 'subsidiary' | 'division' | 'branch' | 'joint_venture' | 'franchise');
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, relationship: rel }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && /^\/api\/entities\/[^/]+\/compliance$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const entityId = path.split('/')[3];
      const statuses = entityManager.getComplianceStatuses(entityId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, statuses }));
      return;
    }
    if (req.method === 'GET' && path === '/api/entities/consolidated-report') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const report = entityManager.getConsolidatedReport();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, report }));
      return;
    }

    // ─── Integration Marketplace Endpoints ──────────────────────────────
    if (req.method === 'GET' && path === '/api/integrations') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const connectors = integrationMarketplace.getEnabledConnectors();
      const stats = integrationMarketplace.getStats();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, connectors: connectors.map(c => ({ id: c.id, name: c.name, category: c.category, frameworks: c.frameworks, capabilities: c.capabilities })), stats }));
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/integrations\/[^/]+\/enable$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      integrationMarketplace.enableConnector(id);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, connectorId: id, enabled: true }));
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/integrations\/[^/]+\/disable$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      integrationMarketplace.disableConnector(id);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, connectorId: id, enabled: false }));
      return;
    }
    if (req.method === 'POST' && path === '/api/integrations/collect') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const jobs = await integrationMarketplace.collectAll();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, jobs, count: jobs.length }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/integrations\/collect\/[^/]+$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[4]!);
      try {
        const job = await integrationMarketplace.collectFromConnector(id);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, job }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/integrations/jobs') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const jobs = integrationMarketplace.getRecentJobs(50);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, jobs, count: jobs.length }));
      return;
    }

    // ─── Policy Management Hub Endpoints ────────────────────────────────
    if (req.method === 'POST' && path === '/api/policies/create') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const policy = policyHub.createPolicy(body as Parameters<typeof policyHub.createPolicy>[0]);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, policy }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/policies') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const policies = policyHub.listPolicies();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, policies, count: policies.length }));
      return;
    }
    if (req.method === 'GET' && path.match(/^\/api\/policies\/[^/]+$/) && !path.includes('/templates') && !path.includes('/stats')) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/').pop()!);
      const policy = policyHub.getPolicy(id);
      if (!policy) { res.writeHead(404); res.end(JSON.stringify({ error: 'not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, policy }));
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/policies\/[^/]+\/approve$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      try {
        const body = await readJson(req);
        const workflow = policyHub.initiateApproval(id, (body.steps as Array<{ assigneeId: string; assigneeName: string; role: string; deadline?: string }>) ?? [], String(body.initiatedBy ?? 'system'));
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, workflow }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/policies\/[^/]+\/publish$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      try {
        const body = await readJson(req);
        const policy = policyHub.publishPolicy(id, String(body.publishedBy ?? 'system'));
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, policy }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/policies\/[^/]+\/attest$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      try {
        const body = await readJson(req);
        const attestations = policyHub.assignAttestation(id, (body.employees as Array<{ employeeId: string; employeeName: string; employeeEmail: string; department: string }>) ?? [], String(body.dueDate ?? new Date(Date.now() + 30 * 86400000).toISOString()));
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, attestations, count: attestations.length }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/policies/templates') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const templates = policyHub.getTemplates();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, templates, count: templates.length }));
      return;
    }
    if (req.method === 'GET' && path === '/api/policies/stats') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const stats = policyHub.getStats();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, stats }));
      return;
    }

    // ─── Vendor Risk Management Endpoints ───────────────────────────────
    if (req.method === 'POST' && path === '/api/vendor-risk/vendors') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const vendor = vendorRiskMgmt.createVendor(body as Parameters<typeof vendorRiskMgmt.createVendor>[0]);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, vendor }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/vendor-risk/vendors') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const vendors = vendorRiskMgmt.listVendors();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, vendors, count: vendors.length }));
      return;
    }
    if (req.method === 'GET' && path.match(/^\/api\/vendor-risk\/vendors\/[^/]+$/) && !path.includes('/risk-score') && !path.includes('/questionnaire') && !path.includes('/monitor')) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/').pop()!);
      const vendor = vendorRiskMgmt.getVendor(id);
      if (!vendor) { res.writeHead(404); res.end(JSON.stringify({ error: 'not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, vendor }));
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/vendor-risk\/vendors\/[^/]+\/questionnaire$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[4]!);
      try {
        const body = await readJson(req);
        const assessment = vendorRiskMgmt.createAssessment(id, String(body.questionnaireId ?? 'qt-sig-lite'));
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, assessment }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path.match(/^\/api\/vendor-risk\/vendors\/[^/]+\/risk-score$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = path.split('/')[4]!;
      const score = vendorRiskMgmt.getRiskScore(id);
      if (!score) { res.writeHead(404); res.end(JSON.stringify({ error: 'not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, score }));
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/vendor-risk\/vendors\/[^/]+\/monitor$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[4]!);
      try {
        vendorRiskMgmt.onboardVendor(id);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, vendorId: id, monitoring: true }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/vendor-risk/alerts') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const alerts = vendorRiskMgmt.getActiveAlerts();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, alerts, count: alerts.length }));
      return;
    }
    if (req.method === 'GET' && path === '/api/vendor-risk/dashboard') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const dashboard = vendorRiskMgmt.getDashboard();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, dashboard }));
      return;
    }

    // ─── Employee Lifecycle Endpoints ───────────────────────────────────
    if (req.method === 'POST' && path === '/api/employees') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const employee = employeeLifecycle.createEmployee(body as Parameters<typeof employeeLifecycle.createEmployee>[0]);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, employee }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/employees') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const url2 = new URL(req.url ?? '', 'http://local');
      const state = url2.searchParams.get('state') as import('@grc-claw/employee-lifecycle').EmployeeState | undefined;
      const department = url2.searchParams.get('department') ?? undefined;
      const employees = employeeLifecycle.listEmployees(state ? { state, department } : undefined);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, employees, count: employees.length }));
      return;
    }
    if (req.method === 'GET' && path.match(/^\/api\/employees\/[^/]+$/) && !path.includes('/compliance-dashboard') && !path.includes('/access-review')) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/').pop()!);
      const employee = employeeLifecycle.getEmployee(id);
      if (!employee) { res.writeHead(404); res.end(JSON.stringify({ error: 'not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, employee }));
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/employees\/[^/]+\/onboard$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      try {
        const workflow = employeeLifecycle.startOnboarding(id);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, workflow }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/employees\/[^/]+\/offboard$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      try {
        const body = await readJson(req).catch(() => ({})) as Record<string, unknown>;
        const workflow = employeeLifecycle.startOffboarding(id, typeof body.targetDate === 'string' ? body.targetDate : undefined);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, workflow }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/employees\/[^/]+\/compliance-check$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      try {
        const compliant = employeeLifecycle.isEmployeeCompliant(id);
        const checks = employeeLifecycle.getEmployeeCompliance(id);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, employeeId: id, compliant, checks }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/employees/compliance-dashboard') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const dashboard = employeeLifecycle.getComplianceDashboard();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, dashboard }));
      return;
    }
    if (req.method === 'POST' && path === '/api/employees/access-review') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const campaign = employeeLifecycle.createAccessReviewCampaign(body as Parameters<typeof employeeLifecycle.createAccessReviewCampaign>[0]);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, campaign }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    // ─── Compliance Task Engine Endpoints ───────────────────────────────
    if (req.method === 'POST' && path === '/api/tasks') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const task = complianceTaskEngine.createTask(body as Parameters<typeof complianceTaskEngine.createTask>[0]);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, task }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/tasks') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const tasks = complianceTaskEngine.listTasks();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, tasks, count: tasks.length }));
      return;
    }
    if (req.method === 'GET' && path.match(/^\/api\/tasks\/[^/]+$/) && !path.includes('/analytics')) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/').pop()!);
      const task = complianceTaskEngine.getTask(id);
      if (!task) { res.writeHead(404); res.end(JSON.stringify({ error: 'not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, task }));
      return;
    }
    if (req.method === 'POST' && path.match(/^\/api\/tasks\/[^/]+\/status$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = decodeURIComponent(path.split('/')[3]!);
      try {
        const body = await readJson(req);
        const statusAction = String(body.action ?? '');
        let task;
        if (statusAction === 'start') task = complianceTaskEngine.startTask(id);
        else if (statusAction === 'complete') task = complianceTaskEngine.completeTask(id);
        else if (statusAction === 'block') task = complianceTaskEngine.blockTask(id, typeof body.reason === 'string' ? body.reason : undefined);
        else if (statusAction === 'cancel') task = complianceTaskEngine.cancelTask(id);
        else { res.writeHead(400); res.end(JSON.stringify({ error: 'invalid_action', validActions: ['start', 'complete', 'block', 'cancel'] })); return; }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, task }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/tasks/bulk-from-findings') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const findings = (body.findings as import('@grc-claw/compliance-task-engine').AuditFinding[]) ?? [];
        const results = complianceTaskEngine.createTasksFromFindings(findings);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, results, count: results.length }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/tasks/analytics') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const analytics = complianceTaskEngine.getAnalytics();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, analytics }));
      return;
    }

    // ─── Evidence Automation Engine Endpoints ───────────────────────────
    if (req.method === 'POST' && path === '/api/evidence-automation/schedule') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const connectorId = String(body.connectorId ?? '');
        const scheduleConfig = body.config as import('@grc-claw/evidence-automation-engine').ScheduleConfig;
        if (!connectorId || !scheduleConfig) { res.writeHead(400); res.end(JSON.stringify({ error: 'connectorId_and_config_required' })); return; }
        const schedule = evidenceAutoEngine.createSchedule(connectorId, scheduleConfig);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, schedule }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/evidence-automation/run-now') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const connectorId = String(body.connectorId ?? '');
        let job;
        if (connectorId) {
          job = await evidenceAutoEngine.collectFromConnector(connectorId);
        } else {
          const jobs = await evidenceAutoEngine.collectAll();
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ ok: true, jobs, count: jobs.length }));
          return;
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, job }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/evidence-automation/history') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const jobs = evidenceAutoEngine.getRecentJobs(50);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, jobs, count: jobs.length }));
      return;
    }
    if (req.method === 'GET' && path === '/api/evidence-automation/gaps') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const gaps = evidenceAutoEngine.detectGaps();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, gaps, count: gaps.length }));
      return;
    }
    if (req.method === 'GET' && path === '/api/evidence-automation/summary') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const summary = evidenceAutoEngine.generateSummaryReport();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, summary }));
      return;
    }

    // ─── OpenAPI Specification Endpoints ────────────────────────────────
    if (req.method === 'GET' && path === '/api/openapi.json') {
      const generator = new OpenAPIGenerator({ baseUrl: `http://${config.host}:${config.port}` });
      generator.addEndpoints(OpenAPIGenerator.buildGatewayEndpoints());
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(generator.toJson());
      return;
    }
    if (req.method === 'GET' && path === '/api/openapi.yaml') {
      const generator = new OpenAPIGenerator({ baseUrl: `http://${config.host}:${config.port}` });
      generator.addEndpoints(OpenAPIGenerator.buildGatewayEndpoints());
      res.writeHead(200, { 'Content-Type': 'text/yaml; charset=utf-8' });
      res.end(generator.toYaml());
      return;
    }

    // ─── Agent Discovery Endpoints ──────────────────────────────────────
    if (req.method === 'POST' && path === '/api/discovery/scan') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const scanner = new AgentDiscoveryScanner({ tenantId: 1 });
        const scanResult = await scanner.scan(basePath());
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, ...scanResult }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(500); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/discovery/inventory') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const scanner = new AgentDiscoveryScanner({ tenantId: 1 });
      await scanner.scan(basePath());
      const inventory = scanner.inventory();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...inventory }));
      return;
    }
    if (req.method === 'GET' && path.match(/^\/api\/discovery\/risk-score\/[^/]+$/)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const agentId = decodeURIComponent(path.split('/').pop()!);
      const scanner = new AgentDiscoveryScanner({ tenantId: 1 });
      await scanner.scan(basePath());
      const score = scanner.riskScore(agentId);
      if (!score) { res.writeHead(404); res.end(JSON.stringify({ error: 'agent_not_found', agentId })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...score }));
      return;
    }

    // ─── Real-time Compliance Dashboard Endpoints ───────────────────────
    if (req.method === 'GET' && path === '/api/dashboard/realtime') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const packs = listFrameworkPacks();
        const frameworkData: Record<string, { compliance_pct: number; drift_detected: boolean; last_scan: string; evidence_count: number; control_count: number }> = {};
        let totalControls = 0;
        let controlsWithEvidence = 0;

        for (const pack of packs) {
          let packTotal = 0;
          let packWithEvidence = 0;
          for (const ctrl of pack.controls) {
            packTotal++;
            totalControls++;
            let hasEvidence = false;
            if (pg) {
              try {
                const items = await evidence.listByControlFromDb(ctrl.id);
                hasEvidence = items.length > 0;
                if (hasEvidence) packWithEvidence++;
              } catch {
                hasEvidence = evidence.listByControl(ctrl.id).length > 0;
                if (hasEvidence) packWithEvidence++;
              }
            } else {
              hasEvidence = evidence.listByControl(ctrl.id).length > 0;
              if (hasEvidence) packWithEvidence++;
            }
          }
          controlsWithEvidence += packWithEvidence;
          frameworkData[pack.code] = {
            compliance_pct: packTotal > 0 ? Math.round((packWithEvidence / packTotal) * 1000) / 10 : 0,
            drift_detected: false,
            last_scan: new Date().toISOString(),
            evidence_count: packWithEvidence,
            control_count: packTotal,
          };
        }

        const autopilotControls = autopilot.getControls();
        const autopilotGaps = autopilot.getGaps();
        const autopilotRemediations = autopilot.getRemediations();
        const autopilotCompliant = autopilotControls.filter((c) => c.status === 'compliant').length;
        const driftHistory = driftDetector.getDriftHistory();
        const driftAlerts = driftDetector.getAlertHistory();
        const baseline = driftDetector.getCurrentBaseline();

        const overallScore = totalControls > 0 ? Math.round((controlsWithEvidence / totalControls) * 1000) / 10 : 0;

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          ok: true,
          timestamp: new Date().toISOString(),
          overall: {
            compliance_score: overallScore,
            total_controls: totalControls,
            controls_with_evidence: controlsWithEvidence,
            controls_without_evidence: totalControls - controlsWithEvidence,
          },
          frameworks: frameworkData,
          autopilot: {
            total_controls: autopilotControls.length,
            compliant: autopilotCompliant,
            non_compliant: autopilotControls.filter((c) => c.status === 'non_compliant').length,
            partial: autopilotControls.filter((c) => c.status === 'partial').length,
            unknown: autopilotControls.filter((c) => c.status === 'unknown').length,
            gaps_count: autopilotGaps.length,
            remediations_count: autopilotRemediations.length,
            is_monitoring: autopilot.isMonitoring(),
          },
          drift: {
            history_count: driftHistory.length,
            alerts_count: driftAlerts.length,
            baseline_captured: baseline !== null,
            baseline_score: baseline?.overallScore ?? null,
            recent_events: driftHistory.slice(-10),
            recent_alerts: driftAlerts.slice(-5),
          },
          websocket: {
            compliance_channel: 'ws://host/ws — subscribe with {"type":"subscribe","channel":"compliance_updates","token":"<token>"}',
            soc_channel: 'ws://host/ws — subscribe with {"type":"subscribe","channel":"soc_events","token":"<token>"}',
          },
        }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(500); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    if (req.method === 'GET' && path === '/api/dashboard/trends') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const url3 = new URL(req.url ?? '', 'http://local');
      const periodDays = Number(url3.searchParams.get('days') ?? '30');
      const packs = listFrameworkPacks();
      const now = Date.now();
      const periodMs = periodDays * 24 * 60 * 60 * 1000;

      const baselineHistory = driftDetector.getBaselineHistory();
      const driftHistory = driftDetector.getDriftHistory();

      const filteredBaselines = baselineHistory.filter((b) => {
        const ts = new Date(b.capturedAt).getTime();
        return ts >= now - periodMs;
      });

      const filteredDrift = driftHistory.filter((d) => {
        const ts = new Date(d.timestamp).getTime();
        return ts >= now - periodMs;
      });

      const dailyScores: Array<{ date: string; score: number; framework_scores: Record<string, number> }> = [];
      for (const baseline of filteredBaselines) {
        dailyScores.push({
          date: baseline.capturedAt.split('T')[0]!,
          score: baseline.overallScore,
          framework_scores: baseline.frameworkScores,
        });
      }

      const driftTrend = filteredDrift.reduce(
        (acc, event) => {
          const date = event.timestamp.split('T')[0]!;
          acc[date] = (acc[date] ?? 0) + 1;
          return acc;
        },
        {} as Record<string, number>,
      );

      const currentControls = autopilot.getControls();
      const gaps = autopilot.getGaps();
      const remediations = autopilot.getRemediations();

      const summary = {
        period_days: periodDays,
        baseline_snapshots: filteredBaselines.length,
        drift_events_total: filteredDrift.length,
        drift_events_by_severity: filteredDrift.reduce(
          (acc, e) => { acc[e.severity] = (acc[e.severity] ?? 0) + 1; return acc;
          },
          {} as Record<string, number>,
        ),
        daily_drift_counts: driftTrend,
        current_compliance: {
          total_controls: currentControls.length,
          compliant: currentControls.filter((c) => c.status === 'compliant').length,
          non_compliant: currentControls.filter((c) => c.status === 'non_compliant').length,
          gaps: gaps.length,
          remediations_pending: remediations.filter((r) => r.status === 'pending').length,
          remediations_completed: remediations.filter((r) => r.status === 'completed').length,
        },
        trend_data: dailyScores,
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...summary }));
      return;
    }

    if (req.method === 'GET' && path === '/api/dashboard/alerts') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const driftAlerts = driftDetector.getAlertHistory();
      const autopilotGaps = autopilot.getGaps();
      const autopilotRemediations = autopilot.getRemediations();

      const activeAlerts: Array<{
        id: string;
        type: 'drift' | 'gap' | 'remediation_failed';
        priority: string;
        severity: string;
        summary: string;
        timestamp: string;
        details: Record<string, unknown>;
      }> = [];

      for (const alert of driftAlerts) {
        activeAlerts.push({
          id: alert.id,
          type: 'drift',
          priority: alert.priority,
          severity: alert.maxSeverity,
          summary: alert.summary,
          timestamp: alert.timestamp,
          details: {
            affectedFrameworks: alert.affectedFrameworks,
            affectedControlCount: alert.affectedControlCount,
            overallScoreDelta: alert.overallScoreDelta,
          },
        });
      }

      for (const gap of autopilotGaps) {
        activeAlerts.push({
          id: gap.id,
          type: 'gap',
          priority: gap.severity === 'critical' ? 'p1' : gap.severity === 'high' ? 'p2' : gap.severity === 'medium' ? 'p3' : 'p4',
          severity: gap.severity,
          summary: `${gap.description} [${gap.framework}]`,
          timestamp: gap.detectedAt,
          details: {
            controlId: gap.controlId,
            controlTitle: gap.controlTitle,
            framework: gap.framework,
            evidenceCount: gap.evidenceCount,
          },
        });
      }

      for (const rem of autopilotRemediations) {
        if (rem.status === 'failed') {
          activeAlerts.push({
            id: rem.id,
            type: 'remediation_failed',
            priority: 'p2',
            severity: 'high',
            summary: `Remediation failed for control ${rem.controlId} [${rem.framework}]`,
            timestamp: rem.createdAt,
            details: {
              gapId: rem.gapId,
              controlId: rem.controlId,
              framework: rem.framework,
              actionsCount: rem.actions.length,
            },
          });
        }
      }

      activeAlerts.sort((a, b) => {
        const priorityOrder: Record<string, number> = { p1: 0, p2: 1, p3: 2, p4: 3 };
        return (priorityOrder[a.priority] ?? 4) - (priorityOrder[b.priority] ?? 4);
      });

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        ok: true,
        total: activeAlerts.length,
        by_type: {
          drift: activeAlerts.filter((a) => a.type === 'drift').length,
          gap: activeAlerts.filter((a) => a.type === 'gap').length,
          remediation_failed: activeAlerts.filter((a) => a.type === 'remediation_failed').length,
        },
        alerts: activeAlerts,
      }));
      return;
    }

    if (req.method === 'GET' && path === '/api/dashboard/kpis') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const packs = listFrameworkPacks();
      let totalControls = 0;
      let controlsWithEvidence = 0;
      for (const pack of packs) {
        for (const ctrl of pack.controls) {
          totalControls++;
          let hasEvidence = false;
          if (pg) {
            try {
              const items = await evidence.listByControlFromDb(ctrl.id);
              hasEvidence = items.length > 0;
            } catch {
              hasEvidence = evidence.listByControl(ctrl.id).length > 0;
            }
          } else {
            hasEvidence = evidence.listByControl(ctrl.id).length > 0;
          }
          if (hasEvidence) controlsWithEvidence++;
        }
      }

      const autopilotControls = autopilot.getControls();
      const autopilotGaps = autopilot.getGaps();
      const autopilotRemediations = autopilot.getRemediations();
      const driftHistory = driftDetector.getDriftHistory();
      const driftAlerts = driftDetector.getAlertHistory();
      const baseline = driftDetector.getCurrentBaseline();
      const ledgerCount = ledger.list(0).length;
      const auditCount = agentAuditTrail.count();

      const complianceScore = totalControls > 0 ? Math.round((controlsWithEvidence / totalControls) * 10000) / 100 : 0;
      const autopilotCompliant = autopilotControls.filter((c) => c.status === 'compliant').length;
      const autopilotTotal = autopilotControls.length;
      const autopilotScore = autopilotTotal > 0 ? Math.round((autopilotCompliant / autopilotTotal) * 10000) / 100 : 0;
      const remediationSuccessRate = autopilotRemediations.length > 0
        ? Math.round((autopilotRemediations.filter((r) => r.status === 'completed' || r.status === 'verified').length / autopilotRemediations.length) * 10000) / 100
        : 0;

      const kpis = {
        compliance: {
          overall_score: complianceScore,
          autopilot_score: autopilotScore,
          total_controls: totalControls,
          controls_with_evidence: controlsWithEvidence,
          evidence_coverage_pct: totalControls > 0 ? Math.round((controlsWithEvidence / totalControls) * 10000) / 100 : 0,
          frameworks_monitored: packs.length,
        },
        autopilot: {
          total_controls: autopilotTotal,
          compliant: autopilotCompliant,
          non_compliant: autopilotControls.filter((c) => c.status === 'non_compliant').length,
          partial: autopilotControls.filter((c) => c.status === 'partial').length,
          gaps_total: autopilotGaps.length,
          gaps_critical: autopilotGaps.filter((g) => g.severity === 'critical').length,
          gaps_high: autopilotGaps.filter((g) => g.severity === 'high').length,
          remediations_total: autopilotRemediations.length,
          remediations_completed: autopilotRemediations.filter((r) => r.status === 'completed').length,
          remediations_pending: autopilotRemediations.filter((r) => r.status === 'pending').length,
          remediation_success_rate: remediationSuccessRate,
          is_monitoring: autopilot.isMonitoring(),
        },
        drift: {
          baseline_captured: baseline !== null,
          baseline_score: baseline?.overallScore ?? null,
          total_events: driftHistory.length,
          events_by_severity: driftHistory.reduce(
            (acc, e) => { acc[e.severity] = (acc[e.severity] ?? 0) + 1; return acc; },
            {} as Record<string, number>,
          ),
          total_alerts: driftAlerts.length,
          alerts_by_priority: driftAlerts.reduce(
            (acc, a) => { acc[a.priority] = (acc[a.priority] ?? 0) + 1; return acc; },
            {} as Record<string, number>,
          ),
        },
        activity: {
          total_tool_invocations: ledgerCount,
          total_audit_records: auditCount,
          agents_tracked: agentAuditTrail.list(0).length > 0
            ? new Set(agentAuditTrail.list(0).map((r) => r.agentDid)).size
            : 0,
        },
        generated_at: new Date().toISOString(),
      };

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, kpis }));
      return;
    }

    if (tryServeConsoleStatic(req, res, path)) return;

    // --- ACCM Endpoints ---
    if (req.method === 'POST' && path === '/api/accm/detect-gaps') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const frameworkCode = String(body.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const gaps = await accmEngine.detectGaps(frameworkCode);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, frameworkCode, gapsDetected: gaps.length, gaps }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/accm/remediate') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const frameworkCode = String(body.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const gaps = await accmEngine.detectGaps(frameworkCode);
        const results = [];
        for (const gap of gaps) {
          const workflow = accmEngine.createRemediationPlan(gap);
          const result = await accmEngine.executeRemediation(workflow);
          results.push({ gapId: gap.id, controlCode: gap.controlCode, workflowId: workflow.id, result });
        }
        // Broadcast compliance update after remediation
        const updatedPosture = await computeCompliancePosture();
        const overallScore = Object.values(updatedPosture).reduce((sum, fw) => sum + (fw as { compliance_pct: number }).compliance_pct, 0) / Math.max(1, Object.keys(updatedPosture).length);
        broadcastComplianceUpdate({
          overall_score: Math.round(overallScore * 10) / 10,
          frameworks: updatedPosture,
          trigger: 'accm_remediate',
          frameworkCode,
          remediationsApplied: results.length,
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, frameworkCode, remediations: results }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/accm/verify') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const workflowId = String(body.workflowId ?? '');
        const workflow = accmEngine.getWorkflow(workflowId);
        if (!workflow) {
          res.writeHead(404); res.end(JSON.stringify({ error: 'workflow_not_found', workflowId }));
          return;
        }
        const verification = await accmEngine.verifyRemediation(workflow);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, verification }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/accm/full-cycle') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const frameworkCode = String(body.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const report = await accmEngine.fullCycle(frameworkCode);
        // Broadcast compliance update to all subscribed clients
        const updatedPosture = await computeCompliancePosture();
        const overallScore = Object.values(updatedPosture).reduce((sum, fw) => sum + (fw as { compliance_pct: number }).compliance_pct, 0) / Math.max(1, Object.keys(updatedPosture).length);
        broadcastComplianceUpdate({
          overall_score: Math.round(overallScore * 10) / 10,
          frameworks: updatedPosture,
          trigger: 'accm_full_cycle',
          frameworkCode,
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, report }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    // --- Agent Builder Endpoints ---
    if (req.method === 'GET' && path === '/api/agents') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const agents = agentBuilder.listAgents();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, agents, count: agents.length }));
      return;
    }
    if (req.method === 'GET' && /^\/api\/agents\/[^/]+$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const agentId = decodeURIComponent(path.split('/').pop()!);
      const agent = agentBuilder.getAgent(agentId);
      if (!agent) { res.writeHead(404); res.end(JSON.stringify({ ok: false, error: 'agent_not_found', agentId })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, agent }));
      return;
    }
    if (req.method === 'POST' && path === '/api/agents') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const definition = body as unknown as AgentDefinition;
        const agent = agentBuilder.createAgent(definition);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, agent }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ ok: false, error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && /^\/api\/agents\/[^/]+\/trigger$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const agentId = decodeURIComponent(path.split('/')[3]!);
      try {
        let body: Record<string, unknown> = {};
        try { body = await readJson(req); } catch { /* empty context is fine */ }
        const run = await agentBuilder.triggerAgent(agentId, body);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, run }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ ok: false, error: msg }));
      }
      return;
    }

    // --- Framework Crosswalk Endpoints ---
    const crosswalkMatch = path.match(/^\/api\/crosswalk\/([^/]+)\/([^/]+)$/);
    if (req.method === 'GET' && crosswalkMatch) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const source = decodeURIComponent(crosswalkMatch[1]!);
      const target = decodeURIComponent(crosswalkMatch[2]!);
      const report = frameworkCrosswalk.generateCrosswalk(source, target);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, report }));
      return;
    }
    if (req.method === 'GET' && path === '/api/crosswalk/overlaps') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const pairs = frameworkCrosswalk.getSupportedPairs();
      const overlaps = pairs.map(([s, t]) => frameworkCrosswalk.findOverlaps(s, t));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, overlaps }));
      return;
    }
    if (req.method === 'POST' && path === '/api/crosswalk/coverage') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const controlIds = (body.controlIds as string[]) ?? [];
        const frameworks = (body.frameworks as string[]) ?? [];
        const coverage = frameworkCrosswalk.calculateMultiFrameworkCoverage(controlIds, frameworks);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, coverage }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    // --- Chat GRC Endpoints ---
    if (req.method === 'POST' && path === '/api/chat') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const message = String(body.message ?? '');
        const context = (body.context as Record<string, unknown>) ?? {};
        const sessionId = typeof body.sessionId === 'string' ? body.sessionId : undefined;
        const chatContext = {
          frameworks: (context.frameworks as string[]) ?? [],
          controls: (context.controls as string[]) ?? [],
          evidence: (context.evidence as string[]) ?? [],
          risks: (context.risks as string[]) ?? [],
        };
        const response = await chatGRC.processMessage(message, chatContext, sessionId);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, response }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/chat/sessions') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const sessions = chatGRC.listSessions();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, sessions }));
      return;
    }
    if (req.method === 'POST' && path === '/api/chat/sessions') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const initialContext = (body.context as Record<string, unknown>) ?? {};
        const chatContext = {
          frameworks: (initialContext.frameworks as string[]) ?? [],
          controls: (initialContext.controls as string[]) ?? [],
          evidence: (initialContext.evidence as string[]) ?? [],
          risks: (initialContext.risks as string[]) ?? [],
        };
        const session = chatGRC.createSession(chatContext);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, session }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    // ─── Board Reporting (#8) ─────────────────────────────────────────────────
    if (req.method === 'GET' && path === '/api/reporting/board') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const reqUrl = new URL(req.url ?? '', 'http://local');
      const type = (reqUrl.searchParams.get('type') ?? 'board_summary') as Parameters<BoardReportGenerator['generateReport']>[0];
      const period = reqUrl.searchParams.get('period') ?? new Date().toISOString().substring(0, 7);
      const report = boardReporter.generateReport(type, period);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, report }));
      return;
    }
    if (req.method === 'GET' && path === '/api/reporting/dashboard') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, dashboard: boardReporter.getExecutiveDashboard() }));
      return;
    }

    // ─── Third-Party Risk (#9) ────────────────────────────────────────────────
    if (req.method === 'GET' && path === '/api/vendors') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, vendors: vendorRegistry.listVendors() }));
      return;
    }
    if (req.method === 'POST' && path === '/api/vendors') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const vendor = vendorRegistry.registerVendor(body as Parameters<VendorRegistry['registerVendor']>[0]);
        vendorRegistry.startMonitoring(vendor.id);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, vendor }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }
    if (req.method === 'GET' && path.startsWith('/api/vendors/') && path.endsWith('/risk-score')) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const vendorId = path.split('/')[3];
      const score = vendorRegistry.calculateRiskScore(vendorId ?? '');
      if (!score) { res.writeHead(404); res.end(JSON.stringify({ error: 'vendor_not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, score }));
      return;
    }

    // ─── Questionnaire Automation (#4) ───────────────────────────────────────
    if (req.method === 'POST' && path === '/api/questionnaire/import') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const csvContent = String(body.csv ?? '');
        if (!csvContent) { res.writeHead(400); res.end(JSON.stringify({ error: 'csv field required' })); return; }
        const questionnaire = questionnaireAutomation.parseCSVQuestions(csvContent);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, questionnaire }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }
    if (req.method === 'POST' && path === '/api/questionnaire/auto-answer') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const questionnaireId = String(body.questionnaireId ?? '');
        const response = questionnaireAutomation.autoAnswer(questionnaireId);
        if (!response) { res.writeHead(404); res.end(JSON.stringify({ error: 'questionnaire_not_found' })); return; }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, response }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }

    // ─── Observability Trace Endpoints ─────────────────────────────────────────
    if (path === '/api/traces' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const url = new URL(req.url ?? '', 'http://local');
      const limit = Number(url.searchParams.get('limit') ?? 50);
      const stats = tracer.getStats();
      const otlp = tracer.exportOTLP();
      const allSpans = otlp.resourceSpans.flatMap((r) => r.scopeSpans.flatMap((s) => s.spans));
      const traceIds = [...new Set(allSpans.map((s) => s.traceId))];
      const recentTraces = traceIds.slice(-limit).map((traceId) => {
        const spans = tracer.getTrace(traceId);
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
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, traces: recentTraces, stats }));
      return;
    }
    if (path === '/api/traces/metrics' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const stats = tracer.getStats();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        ok: true,
        metrics: {
          totalTraces: stats.totalTraces,
          totalSpans: stats.totalSpans,
          avgSpanDurationMs: stats.avgSpanDurationMs,
          errorRate: Math.round(stats.errorRate * 10000) / 100,
          totalMetricEvents: stats.totalMetrics,
        },
      }));
      return;
    }
    const traceDetailMatch = path.match(/^\/api\/traces\/([^/]+)$/);
    if (traceDetailMatch && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const traceId = decodeURIComponent(traceDetailMatch[1]!);
      const spans = tracer.getTrace(traceId);
      if (spans.length === 0) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: 'trace_not_found', traceId }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, traceId, spans }));
      return;
    }

    // ─── ZK Proof Generation (#6) ─────────────────────────────────────────────
    if (req.method === 'POST' && path === '/api/zk/prove') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req) as { controlId: string; frameworkCode: string; controlStatus: string; evidenceHashes: string[] };
        const proof = await complianceProver.generateProof({
          controlId: body.controlId,
          frameworkCode: body.frameworkCode,
          controlStatus: body.controlStatus,
          evidenceHashes: body.evidenceHashes ?? [],
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, proof }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }
    if (req.method === 'POST' && path === '/api/zk/verify') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req) as unknown as Parameters<ComplianceProver['verifyProof']>[0];
        const result = await complianceProver.verifyProof(body);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }

    // ─── Compliance Autopilot Endpoints ───────────────────────────────────
    if (path === '/api/autopilot/run-cycle' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const cycle = await autopilot.runCycle();
        broadcastComplianceUpdate({
          overall_score: cycle.report?.complianceScore ?? 0,
          frameworks: { autopilot: { compliance_pct: cycle.report?.complianceScore ?? 0, drift_detected: cycle.monitor.gapsFound > 0, last_scan: new Date().toISOString() } },
          trigger: 'autopilot_cycle',
          cycleId: cycle.cycleId,
          gapsFound: cycle.monitor.gapsFound,
          remediations: cycle.remediations.length,
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, cycle }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (path === '/api/autopilot/monitoring-status' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, monitoring: autopilot.isMonitoring(), intervalMs: autopilot.getConfig().monitorIntervalMs }));
      return;
    }
    if (path === '/api/autopilot/stop-monitoring' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      autopilot.stopMonitoring();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, monitoring: false }));
      return;
    }
    if (path === '/api/autopilot/status' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const controls = autopilot.getControls();
      const gaps = autopilot.getGaps();
      const remediations = autopilot.getRemediations();
      const compliant = controls.filter(c => c.status === 'compliant').length;
      const total = controls.length;
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        ok: true,
        complianceScore: total > 0 ? Math.round((compliant / total) * 10000) / 100 : 0,
        totalControls: total,
        compliantControls: compliant,
        gapsCount: gaps.length,
        remediationsCount: remediations.length,
        frameworks: autopilot.getConfig().frameworks,
        controls: controls.map(c => ({ id: c.id, controlId: c.controlId, framework: c.framework, status: c.status, title: c.title })),
        gaps,
      }));
      return;
    }
    const autopilotReportMatch = path.match(/^\/api\/autopilot\/report\/([^/]+)$/);
    if (autopilotReportMatch && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const framework = decodeURIComponent(autopilotReportMatch[1]!);
      try {
        const report = await autopilot.generateReport(framework);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, report }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (path === '/api/autopilot/audit-trail' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const auditTrail = autopilot.getAuditTrail();
      const verified = autopilot.verifyAuditTrail();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, auditTrail, verified, count: auditTrail.length }));
      return;
    }

    // ─── Drift Detector Endpoints ──────────────────────────────────────
    if (req.method === 'POST' && path === '/api/drift/capture-baseline') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const baseline = await driftDetector.captureBaseline();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, baseline }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/drift/detect') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const result = await driftDetector.detectDrift();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/drift/history') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const history = driftDetector.getDriftHistory();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, history, count: history.length }));
      return;
    }
    if (req.method === 'GET' && path === '/api/drift/alerts') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const alerts = driftDetector.getAlertHistory();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, alerts, count: alerts.length }));
      return;
    }

    // ─── Evidence Collector Endpoints ──────────────────────────────────
    if (req.method === 'POST' && path === '/api/evidence/collect') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const framework = String(body.framework ?? 'SOC2') as ECFramework;
        const category = String(body.category ?? 'mfa');
        const controlId = String(body.controlId ?? 'default');
        const result = await evidenceCollector.collect([{ category: category as any, framework, controlId }]);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/evidence/inventory') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const inventory = evidenceCollector.getAllEvidence();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, inventory, count: inventory.length }));
      return;
    }
    const evidenceSummaryMatch = path.match(/^\/api\/evidence\/summary\/([^/]+)$/);
    if (req.method === 'GET' && evidenceSummaryMatch) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const framework = decodeURIComponent(evidenceSummaryMatch[1]!) as ECFramework;
      const summary = evidenceCollector.getComplianceSummary(framework);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, framework, summary }));
      return;
    }

    // ─── Agent Audit Trail Endpoints ─────────────────────────────
    if (path === '/api/audit-trail' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const url = new URL(req.url ?? '', 'http://local');
      const limit = Number(url.searchParams.get('limit') ?? 100);
      const records = agentAuditTrail.list(limit);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, records, count: records.length, total: agentAuditTrail.count() }));
      return;
    }
    if (path === '/api/audit-trail/verify' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const result = agentAuditTrail.verify();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...result }));
      return;
    }
    if (path === '/api/audit-trail/export' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const url = new URL(req.url ?? '', 'http://local');
      const format = (url.searchParams.get('format') ?? 'json') as 'json' | 'csv';
      const agentDid = url.searchParams.get('agentDid') ?? undefined;
      const toolFilter = url.searchParams.get('tool') ?? undefined;
      const from = url.searchParams.get('from') ?? undefined;
      const to = url.searchParams.get('to') ?? undefined;
      const exported = agentAuditTrail.export({ format, agentDid, tool: toolFilter, from, to });
      if (format === 'csv') {
        res.writeHead(200, { 'Content-Type': 'text/csv' });
      } else {
        res.writeHead(200, { 'Content-Type': 'application/json' });
      }
      res.end(exported);
      return;
    }
    const auditTrailDetailMatch = path.match(/^\/api\/audit-trail\/([^/]+)$/);
    if (auditTrailDetailMatch && req.method === 'GET' && !path.includes('verify') && !path.includes('export')) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const recordId = decodeURIComponent(auditTrailDetailMatch[1]!);
      const records = agentAuditTrail.list();
      const record = records.find(r => r.id === recordId);
      if (!record) { res.writeHead(404); res.end(JSON.stringify({ ok: false, error: 'record_not_found', recordId })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, record }));
      return;
    }

    // ─── RBAC Auth Endpoints ────────────────────────────────────────
    if (path === '/api/auth/login' && req.method === 'POST') {
      let body: Record<string, unknown>;
      try {
        body = await readJson(req);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'invalid_body';
        const status = msg === 'request_body_too_large' ? 413 : 400;
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
        return;
      }
      const userId = String(body.userId ?? body.user_id ?? '');
      const tenantId = String(body.tenantId ?? body.tenant_id ?? defaultTenant.id);
      if (!userId) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'userId_required' }));
        return;
      }
      // Auto-assign viewer role if user has no roles
      const existingRoles = rbacEngine.getUserRoles(userId, tenantId);
      if (existingRoles.length === 0) {
        rbacEngine.assignRole(userId, 'viewer', 'global', tenantId, 'system');
      }
      const token = rbacEngine.generateJWT(userId, tenantId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, token, userId, tenantId }));
      return;
    }

    if (path === '/api/auth/refresh' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const gwReq = req as GatewayRequest;
      const tc = gwReq.tenantContext;
      if (!tc?.userId || !tc?.tenantId) {
        res.writeHead(401, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'no_tenant_context' }));
        return;
      }
      const newToken = rbacEngine.generateJWT(tc.userId, tc.tenantId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, token: newToken, userId: tc.userId, tenantId: tc.tenantId }));
      return;
    }

    if (path === '/api/auth/me' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const gwReq = req as GatewayRequest;
      const tc = gwReq.tenantContext;
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        ok: true,
        userId: tc?.userId ?? 'unknown',
        tenantId: tc?.tenantId ?? 'unknown',
        role: tc?.role ?? 'unknown',
        scope: tc?.scope ?? 'unknown',
        permissions: tc?.permissions ?? [],
      }));
      return;
    }

    if (path === '/api/auth/roles' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const roles = rbacEngine.getAllRoles();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, roles, count: roles.length }));
      return;
    }

    if (path === '/api/auth/roles' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      let body: Record<string, unknown>;
      try {
        body = await readJson(req);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'invalid_body';
        const status = msg === 'request_body_too_large' ? 413 : 400;
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
        return;
      }
      const userId = String(body.userId ?? '');
      const role = String(body.role ?? 'viewer') as import('@grc-claw/rbac-multi-tenant').RoleName;
      const tenantId = String(body.tenantId ?? defaultTenant.id);
      const scope = (String(body.scope ?? 'global') as import('@grc-claw/rbac-multi-tenant').ScopeLevel);
      const gwReq = req as GatewayRequest;
      const assignedBy = gwReq.tenantContext?.userId ?? 'system';
      if (!userId) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'userId_required' }));
        return;
      }
      try {
        const assignment = rbacEngine.assignRole(userId, role, scope, tenantId, assignedBy);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, assignment }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    if (path === '/api/auth/audit' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const gwReq = req as GatewayRequest;
      const url = new URL(req.url ?? '', 'http://local');
      const limit = Number(url.searchParams.get('limit') ?? 100);
      const tenantFilter = url.searchParams.get('tenantId') ?? gwReq.tenantContext?.tenantId;
      const logs = rbacEngine.getAuditLog(tenantFilter ?? undefined, limit);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, logs, count: logs.length }));
      return;
    }

    // ─── Terraform Provider Endpoints ───────────────────────────────
    if (path === '/api/terraform/plan' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const config = body as unknown as import('@grc-claw/terraform-provider').TerraformResourceConfig;
        const plan = terraformProvider.plan(config);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, plan }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    if (path === '/api/terraform/apply' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const config = body as unknown as import('@grc-claw/terraform-provider').TerraformResourceConfig;
        const result = terraformProvider.apply(config);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    if (path === '/api/terraform/destroy' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const resourceType = String(body.resourceType ?? body.type ?? '') as import('@grc-claw/terraform-provider').TerraformResourceType;
        const name = String(body.name ?? '');
        if (!resourceType || !name) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'resourceType_and_name_required' }));
          return;
        }
        const deleted = terraformProvider.destroy(resourceType, name);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, deleted, resourceType, name }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    if (path === '/api/terraform/import' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const resourceType = String(body.resourceType ?? body.type ?? '') as import('@grc-claw/terraform-provider').TerraformResourceType;
        const name = String(body.name ?? '');
        const id = String(body.id ?? '');
        const attributes = (body.attributes as Record<string, unknown>) ?? {};
        if (!resourceType || !name || !id) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'resourceType_name_and_id_required' }));
          return;
        }
        const result = terraformProvider.importResource(resourceType, name, id, attributes);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    if (path === '/api/terraform/state' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const url = new URL(req.url ?? '', 'http://local');
      const resourceType = url.searchParams.get('type') as import('@grc-claw/terraform-provider').TerraformResourceType | undefined;
      const name = url.searchParams.get('name');
      if (resourceType && name) {
        const state = terraformProvider.getState(resourceType, name);
        if (!state) {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ ok: false, error: 'state_not_found', resourceType, name }));
          return;
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, state }));
      } else {
        const states = terraformProvider.listStates(resourceType);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, states, count: states.length }));
      }
      return;
    }

    if (path === '/api/terraform/resources' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const types = terraformProvider.getResourceTypes();
      const dataTypes = terraformProvider.getDataSourceTypes();
      const states = terraformProvider.listStates();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, resourceTypes: types, dataSourceTypes: dataTypes, states, count: states.length }));
      return;
    }

    // ─── Continuous Trust Engine ──────────────────────────────────────────
    if (path === '/api/trust/score' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const score = continuousTrustEngine.getScore();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, score }));
      return;
    }

    if (path === '/api/trust/history' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const trustUrl = new URL(req.url ?? '', 'http://local');
      const hours = Number(trustUrl.searchParams.get('hours') ?? 24);
      const history = continuousTrustEngine.getHistory(hours);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, history, count: history.length }));
      return;
    }

    if (path === '/api/trust/alerts' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const alerts = continuousTrustEngine.getAlerts();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, alerts, count: alerts.length }));
      return;
    }

    // ─── Agent Collaboration ──────────────────────────────────────────────
    if (path === '/api/collaboration/sessions' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const sessions = agentCollaboration.getActiveSessions();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, sessions, count: sessions.length }));
      return;
    }

    if (path === '/api/collaboration/agents' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const agents = agentCollaboration.getAvailableAgents([]);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, agents, count: agents.length }));
      return;
    }

    // ─── Regulatory Change Management ─────────────────────────────────────
    if (path === '/api/regulatory/changes' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const regUrl = new URL(req.url ?? '', 'http://local');
      const framework = regUrl.searchParams.get('framework') ?? undefined;
      const severity = regUrl.searchParams.get('severity') ?? undefined;
      const status = regUrl.searchParams.get('status') ?? undefined;
      const changes = regulatoryChangeMgmt.getChanges({ framework, severity, status });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, changes, count: changes.length }));
      return;
    }

    if (path === '/api/regulatory/gaps' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const gapsUrl = new URL(req.url ?? '', 'http://local');
      const framework = gapsUrl.searchParams.get('framework') ?? undefined;
      const status = gapsUrl.searchParams.get('status') ?? undefined;
      const gaps = regulatoryChangeMgmt.getGaps({ framework, status });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, gaps, count: gaps.length }));
      return;
    }

    if (path === '/api/regulatory/sources' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const sources = regulatoryChangeMgmt.getSources();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, sources, count: sources.length }));
      return;
    }

    // ─── AI Governance ────────────────────────────────────────────────────
    if (path === '/api/ai-governance/systems' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const aiUrl = new URL(req.url ?? '', 'http://local');
      const riskClass = aiUrl.searchParams.get('riskClass') ?? undefined;
      const status = aiUrl.searchParams.get('status') ?? undefined;
      const systems = aiGovernance.getSystems({ riskClass, status });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, systems, count: systems.length }));
      return;
    }

    if (path === '/api/ai-governance/dashboard' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const dashboard = aiGovernance.getDashboardData();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, dashboard }));
      return;
    }

    // ─── Compliance Knowledge Graph ───────────────────────────────────────
    if (path === '/api/knowledge-graph/summary' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const summary = complianceKnowledgeGraph.analytics.getSummary();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, summary }));
      return;
    }

    if (path === '/api/knowledge-graph/posture' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const postureUrl = new URL(req.url ?? '', 'http://local');
      const organizationId = postureUrl.searchParams.get('organizationId') ?? 'demo-org';
      const posture = complianceKnowledgeGraph.analytics.calculatePosture(organizationId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, posture }));
      return;
    }

    if (path === '/api/knowledge-graph/crosswalk' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const crosswalkUrl = new URL(req.url ?? '', 'http://local');
      const from = crosswalkUrl.searchParams.get('from') ?? '';
      const to = crosswalkUrl.searchParams.get('to') ?? '';
      const mappings = to
        ? complianceKnowledgeGraph.query
            .getCrosswalk(from)
            .filter((mapping) => mapping.targetFrameworkId === to || mapping.targetControlId === to)
        : complianceKnowledgeGraph.query.getCrosswalk(from);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, mappings, count: mappings.length }));
      return;
    }

    // ─── Predictive Compliance ────────────────────────────────────────────
    if (path === '/api/predictive/forecasts' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const forecasts = predictiveCompliance.forecastAll();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, forecasts, count: forecasts.length }));
      return;
    }

    if (path === '/api/predictive/risks' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const risks = predictiveCompliance.rankByRisk();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, risks, count: risks.length }));
      return;
    }

    // ─── Compliance Marketplace ───────────────────────────────────────────
    if (path === '/api/marketplace/stats' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const stats = complianceMarketplace.stats();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, stats }));
      return;
    }

    if (path === '/api/marketplace/packs' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const marketplaceUrl = new URL(req.url ?? '', 'http://local');
      const framework = marketplaceUrl.searchParams.get('framework') ?? undefined;
      const industry = marketplaceUrl.searchParams.get('industry') ?? undefined;
      const packs = complianceMarketplace.search({
        frameworks: framework ? [framework] : undefined,
        industries: industry ? [industry] : undefined,
        limit: Number(marketplaceUrl.searchParams.get('limit') ?? 50),
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, packs, count: packs.length }));
      return;
    }

    // ─── Zero Trust Audit ─────────────────────────────────────────────────
    if (path === '/api/audit/verify' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const verification = zeroTrustAudit.verify();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, verification }));
      return;
    }

    if (path === '/api/audit/records' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const records = zeroTrustAudit.getRecords();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, records, count: records.length }));
      return;
    }

    // ─── Evidence Graph ──────────────────────────────────────────────────
    if (path === '/api/evidence-graph' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const evidenceGraphUrl = new URL(req.url ?? '', 'http://local');
      const organizationId = evidenceGraphUrl.searchParams.get('organizationId') ?? 'demo-org';
      const graph = buildEvidenceGraphSnapshot(organizationId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(graph));
      return;
    }

    if (path === '/api/evidence-graph/summary' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const evidenceGraphUrl = new URL(req.url ?? '', 'http://local');
      const organizationId = evidenceGraphUrl.searchParams.get('organizationId') ?? 'demo-org';
      const graph = buildEvidenceGraphSnapshot(organizationId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, graph_hash: graph.graph_hash, generated_at: graph.generated_at, summary: graph.summary }));
      return;
    }

    if (path === '/api/evidence-graph/nodes' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const evidenceGraphUrl = new URL(req.url ?? '', 'http://local');
      const organizationId = evidenceGraphUrl.searchParams.get('organizationId') ?? 'demo-org';
      const graph = buildEvidenceGraphSnapshot(organizationId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, graph_hash: graph.graph_hash, nodes: graph.nodes, count: graph.nodes.length }));
      return;
    }

    if (path === '/api/evidence-graph/edges' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const evidenceGraphUrl = new URL(req.url ?? '', 'http://local');
      const organizationId = evidenceGraphUrl.searchParams.get('organizationId') ?? 'demo-org';
      const graph = buildEvidenceGraphSnapshot(organizationId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, graph_hash: graph.graph_hash, edges: graph.edges, count: graph.edges.length }));
      return;
    }

    // ─── Federated Learning ───────────────────────────────────────────────
    if (path === '/api/federated/status' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const status = { message: 'Federated learning network active' };
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, status }));
      return;
    }

    // ─── Compliance Intelligence ──────────────────────────────────────────
    if (path === '/api/intelligence/trends' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const trends = complianceIntelligence.getAllTrends();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, trends }));
      return;
    }

    if (path === '/api/intelligence/benchmarks' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const benchmarks = complianceIntelligence.getNetworkSnapshot();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, benchmarks }));
      return;
    }

    if (path === '/api/intelligence/recommendations' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const recsUrl = new URL(req.url ?? '', 'http://local');
      const orgId = recsUrl.searchParams.get('orgId') ?? 'default';
      const recommendations = complianceIntelligence.getRecommendations(orgId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, recommendations }));
      return;
    }

    // ─── Autonomous Compliance Agent ──────────────────────────────────────
    if (path === '/api/autonomous/scan' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, message: 'Scan requires async execution' }));
      return;
    }

    if (path === '/api/autonomous/issues' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const issues = autonomousAgent.getScanResults();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, issues, count: issues.length }));
      return;
    }

    // ─── Compliance Digital Twin ──────────────────────────────────────────
    if (path === '/api/digital-twin/status' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const twins = complianceDigitalTwin.listTwins();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, twins, count: twins.length }));
      return;
    }

    if (path === '/api/digital-twin/forecast' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const forecastUrl = new URL(req.url ?? '', 'http://local');
      const twinId = forecastUrl.searchParams.get('twinId') ?? 'default';
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, message: 'Forecast requires twin ID and parameters' }));
      return;
    }

    // ─── Quantum-Resistant Crypto ─────────────────────────────────────────
    if (path === '/api/crypto/hybrid-encrypt' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, message: 'Hybrid encryption requires async execution' }));
      return;
    }

    if (path === '/api/crypto/sign' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, message: 'Signing requires async execution' }));
      return;
    }

    // ─── Natural Language Compliance ──────────────────────────────────────
    if (path === '/api/nl-compliance/ask' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const nlBody = await readJson(req);
      const question = String(nlBody.question ?? '');
      const answer = nlCompliance.ask(question);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, answer }));
      return;
    }

    if (path === '/api/nl-compliance/report' && req.method === 'POST') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const reportBody = await readJson(req);
      const framework = String(reportBody.framework ?? 'soc2') as any;
      const report = nlCompliance.generateReport([framework]);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, report }));
      return;
    }

    // ─── Compliance Automation Marketplace ────────────────────────────────
    if (path === '/api/automation-marketplace/stats' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const publisherList = automationMarketplace.publisher.list();
      const stats = { total: publisherList.length, published: publisherList.filter(a => a.status === 'published').length };
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, stats }));
      return;
    }

    if (path === '/api/automation-marketplace/search' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, message: 'Search requires async execution' }));
      return;
    }

    // ─── Real-Time Compliance Monitor ─────────────────────────────────────
    if (path === '/api/realtime/status' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const slaStatus = realTimeMonitor.slaMonitor.getStatus();
      const breaches = realTimeMonitor.slaMonitor.getBreaches();
      const status = { slaStatus: Object.fromEntries(slaStatus), breachCount: breaches.length };
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, status }));
      return;
    }

    if (path === '/api/realtime/alerts' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const alerts = realTimeMonitor.alertEngine.getAlerts();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, alerts, count: alerts.length }));
      return;
    }

    res.writeHead(404);
    res.end(JSON.stringify({ error: 'not_found' }));
  });

  const wss = new WebSocketServer({ server: httpServer });
  wss.on('connection', (socket: WebSocket) => {
    let connected = false;
    socket.on('message', (raw) => {
      try {
        const frame = JSON.parse(String(raw)) as {
          type: string;
          channel?: string;
          token?: string;
          params?: { auth?: { token?: string }; role?: string };
        };
        if (!connected && frame.type === 'connect') {
          const token = frame.params?.auth?.token ?? '';
          const secretBuf = Buffer.from(config.token, 'utf8');
          const tokenBuf = Buffer.from(token, 'utf8');
          const tokenValid = secretBuf.length === tokenBuf.length && timingSafeEqual(secretBuf, tokenBuf);
          if (!tokenValid) {
            const wsIp = (socket as unknown as { _socket?: { remoteAddress?: string } })._socket?.remoteAddress ?? 'unknown';
            console.warn(
              `[SECURITY] auth_failure ip=${wsIp} reason=ws_token_mismatch endpoint=/ws timestamp=${new Date().toISOString()}`
            );
            socket.close(4001, 'unauthorized');
            return;
          }
          connected = true;
          socket.send(JSON.stringify({ type: 'hello-ok', role: frame.params?.role ?? 'operator' }));
          return;
        }
        if (frame.type === 'subscribe' && frame.channel === 'soc_events') {
          const token = frame.token ?? '';
          const secretBuf = Buffer.from(config.token, 'utf8');
          const tokenBuf = Buffer.from(token, 'utf8');
          const authed = secretBuf.length === tokenBuf.length && timingSafeEqual(secretBuf, tokenBuf);
          if (authed) {
            socClients.add(socket);
            socket.send(JSON.stringify({ type: 'subscribed', channel: 'soc_events', message: 'Streaming normalized SOC events' }));
          } else {
            socket.send(JSON.stringify({ type: 'error', message: 'unauthorized' }));
          }
          return;
        }
        if (frame.type === 'subscribe' && frame.channel === 'compliance_updates') {
          const token = frame.token ?? '';
          const secretBuf = Buffer.from(config.token, 'utf8');
          const tokenBuf = Buffer.from(token, 'utf8');
          const authed = secretBuf.length === tokenBuf.length && timingSafeEqual(secretBuf, tokenBuf);
          if (authed) {
            complianceClients.add(socket);
            // Send initial compliance posture immediately on subscription
            computeCompliancePosture().then((initialPosture) => {
              const overallScore = Object.values(initialPosture).reduce((sum, fw) => sum + (fw as { compliance_pct: number }).compliance_pct, 0) / Math.max(1, Object.keys(initialPosture).length);
              socket.send(JSON.stringify({
                type: 'compliance_update',
                data: { overall_score: Math.round(overallScore * 10) / 10, frameworks: initialPosture, ts: new Date().toISOString() },
                ts: new Date().toISOString(),
              }));
            }).catch(() => {});
            socket.send(JSON.stringify({ type: 'subscribed', channel: 'compliance_updates', message: 'Streaming real-time compliance updates' }));
          } else {
            socket.send(JSON.stringify({ type: 'error', message: 'unauthorized' }));
          }
          return;
        }
        if (!connected) {
          socket.close(4000, 'connect_required');
        }
      } catch {
        socket.close(4002, 'invalid_frame');
      }
    });
    socket.on('close', () => { socClients.delete(socket); complianceClients.delete(socket); });
    socket.on('error', () => { socClients.delete(socket); complianceClients.delete(socket); });
  });

  // ─── Periodic SOC heartbeat — broadcast real compliance posture to subscribers ───
  async function computeCompliancePosture(): Promise<Record<string, { compliance_pct: number; drift_detected: boolean; last_scan: string }>> {
    const packs = listFrameworkPacks();
    const frameworks: Record<string, { compliance_pct: number; drift_detected: boolean; last_scan: string }> = {};
    for (const pack of packs) {
      let total = 0;
      let withEvidence = 0;
      for (const ctrl of pack.controls) {
        total++;
        let hasEvidence = false;
        if (pg) {
          try {
            const items = await evidence.listByControlFromDb(ctrl.id);
            hasEvidence = items.length > 0;
          } catch {
            hasEvidence = evidence.listByControl(ctrl.id).length > 0;
          }
        } else {
          hasEvidence = evidence.listByControl(ctrl.id).length > 0;
        }
        if (hasEvidence) withEvidence++;
      }
      frameworks[pack.code] = {
        compliance_pct: total > 0 ? Math.round((withEvidence / total) * 1000) / 10 : 0,
        drift_detected: false,
        last_scan: new Date().toISOString(),
      };
    }
    return frameworks;
  }

  const heartbeatInterval = setInterval(() => {
    if (socClients.size === 0) return;
    broadcastSocEvent({
      type: 'heartbeat',
      id: `heartbeat-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      status: 'alive',
      node_id: `gateway-${config.host}:${config.port}`,
    });
  }, 60_000);

  // ─── Start drift detector polling ─────────────────────────────────────
  driftDetector.startPolling();

  // ─── Compliance posture summary — broadcast every 5 minutes ─────────────────
  const postureInterval = setInterval(async () => {
    if (socClients.size === 0 && complianceClients.size === 0) return;
    const posture = await computeCompliancePosture();
    const overallScore = Object.values(posture).reduce((sum, fw) => sum + (fw as { compliance_pct: number }).compliance_pct, 0) / Math.max(1, Object.keys(posture).length);
    const complianceUpdate = {
      type: 'posture_update',
      id: `posture-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      frameworks: posture,
      node_id: `gateway-${config.host}:${config.port}`,
    };
    broadcastSocEvent(complianceUpdate);
    broadcastComplianceUpdate({
      overall_score: Math.round(overallScore * 10) / 10,
      frameworks: posture,
      trigger: 'periodic_heartbeat',
    });
    }, 300_000);

  // ─── Auto-start periodic compliance monitoring on boot (5 min) ────────
  autopilot.startMonitoring(300_000);

  return {
    listen: () =>
      new Promise<void>((resolve) => {
        httpServer.listen(config.port, config.host, () => resolve());
      }),
    close: async () => {
      driftDetector.stopPolling();
      clearInterval(heartbeatInterval);
      clearInterval(postureInterval);
      await closePersistence();
      return new Promise<void>((resolve, reject) => {
        wss.close(() => httpServer.close((e) => (e ? reject(e) : resolve())));
      });
    },
    evidence,
    a2z,
    refreshExecPolicy,
    persistence: pg,
  };
}

function basePath(): string {
  return process.env.GRC_CLAW_SCAN_ROOT?.trim() || process.cwd();
}

function toolTierFor(tool: string): ToolTier {
  return BUILTIN_AGENT_TOOLS.find((definition) => definition.name === tool)?.tier
    ?? (tool.includes('delete') || tool.includes('destroy') ? 'destructive' : 'read');
}

function readJson(req: IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let totalBytes = 0;
    req.on('data', (c: Buffer) => {
      totalBytes += c.length;
      if (totalBytes > MAX_BODY_BYTES) {
        req.destroy();
        reject(new Error('request_body_too_large'));
        return;
      }
      chunks.push(c);
    });
    req.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

function validateBody(
  body: Record<string, unknown>,
  requiredFields: string[]
): { valid: boolean; missing?: string } {
  for (const field of requiredFields) {
    if (!(field in body)) {
      return { valid: false, missing: field };
    }
  }
  return { valid: true };
}
