import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  createTrustTransaction,
  hashTrustTransaction,
  verifyTrustTransaction,
  type TrustTransactionEnvelope,
  type NewTrustTransaction,
} from '../../trust-transaction/src/index.ts';
import {
  AgentPolicyFirewall,
  formatFirewallReceiptForEvidenceGraph,
  type FirewallActor,
  type FirewallToolRequest,
  type FirewallContext,
} from '../../agent-policy-firewall/src/index.ts';
import {
  buildProcurementPacket,
  verifyProcurementPacket,
  calculateSprsScore,
  type ProcurementPacket,
} from '../../defense-procurement/src/index.ts';
import {
  createVerifierRoom,
  verifyRoomAccess,
  createVerifierEvent,
  buildVerifierExportPacket,
  type VerifierRoom,
  type VerifierIdentity,
} from '../../verifier-network/src/index.ts';
import {
  createBenchmarkSignal,
  aggregateBenchmarkSignals,
  computeOverallScore,
  type BenchmarkSignal,
} from '../../benchmark-intelligence/src/index.ts';
import {
  FrameworkCrosswalk,
} from '../../framework-crosswalk/src/FrameworkCrosswalk.ts';
import {
  nodeObject,
  edgeObject,
  objectsToSnapshot,
  evidenceObjectHash,
  type EvidenceGraphObject,
} from '../../evidence-graph/src/index.ts';
import { AgentTrustScoreEngine } from '../../agent-trust-score/src/index.ts';
import type { TrustCredential, BehavioralSignal } from '../../agent-trust-score/src/types.ts';
import type { CredentialStore } from '../../agent-trust-score/src/credentials/TrustCredentialIssuer.ts';

// ---------------------------------------------------------------------------
// Deterministic timestamp
// ---------------------------------------------------------------------------

const FIXED_TS = '2026-06-30T00:00:00.000Z';

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function makeActor(overrides: Partial<FirewallActor> = {}): FirewallActor {
  return {
    id: 'agent:test-runner',
    type: 'agent',
    tenantId: 1,
    orgSlug: 'acme-corp',
    role: 'reader',
    trustScore: 85,
    ...overrides,
  };
}

function makeContext(overrides: Partial<FirewallContext> = {}): FirewallContext {
  return {
    tenantScope: ['evidence', 'controls'],
    role: 'reader',
    allowedTools: ['evidence.collect', 'evidence.list'],
    deniedTools: ['admin.drop_table'],
    sandboxPolicy: 'docker',
    approvalThreshold: 'human',
    dataBoundary: 'tenant-confidential',
    replayWindowSeconds: 300,
    maxBlastRadius: 10,
    controlImpactIds: ['AC.L1-3.1.1'],
    ...overrides,
  };
}

function makeRequest(overrides: Partial<FirewallToolRequest> = {}): FirewallToolRequest {
  return {
    toolName: 'evidence.collect',
    tier: 'read',
    args: { controlId: 'AC.L1-3.1.1' },
    idempotencyKey: 'idem-001',
    ...overrides,
  };
}

function makeVerifier(overrides: Partial<VerifierIdentity> = {}): VerifierIdentity {
  return {
    verifierId: 'ver-001',
    name: 'Jane Auditor',
    email: 'jane@example.com',
    organization: 'Big4 Audit',
    role: 'auditor',
    scope: 'auditor',
    ...overrides,
  };
}

const mockCredentialStore: CredentialStore = {
  async store(): Promise<void> {},
  async get(): Promise<TrustCredential | undefined> {
    return undefined;
  },
  async listByAgent(): Promise<TrustCredential[]> {
    return [];
  },
  async revoke(): Promise<boolean> {
    return true;
  },
};

function baseTxInput(overrides: Partial<NewTrustTransaction> = {}): NewTrustTransaction {
  return {
    kind: 'agent_intent',
    status: 'approved',
    tenantId: 72,
    orgSlug: 'a2z-soc',
    actor: { id: 'agent:grc-copilot', type: 'agent', tenantId: 72, did: 'did:grc:copilot' },
    action: {
      name: 'collect_evidence',
      tool: 'evidence.collect',
      idempotencyKey: 'collect-evidence-001',
      correlationId: 'case-001',
    },
    policy: {
      policyId: 'agent-policy-firewall/default',
      decision: 'allow',
      sandboxPolicy: 'tenant-read-write-no-secrets',
      approvalThreshold: 'human',
      replayWindowSeconds: 300,
      rollbackPlanId: 'rollback:evidence-collect',
    },
    dataBoundary: 'tenant-confidential',
    evidence: {
      graphId: 'graph:evidence:001',
      graphObjectHash: 'hash:graph-object',
      controlIds: ['AC.L1-3.1.1'],
      frameworkCodes: ['CMMC', 'NIST-800-171'],
    },
    exportTargets: ['evidence_graph', 'verifier_room'],
    createdAt: FIXED_TS,
    ...overrides,
  };
}

function minimalPacket(overrides: Partial<ProcurementPacket> = {}): Omit<ProcurementPacket, 'version' | 'packetHash'> {
  return {
    packetId: 'procurement:acme:prime_contractor:abc123',
    createdAt: FIXED_TS,
    tenantId: 1,
    orgSlug: 'acme-corp',
    packetMode: 'prime_contractor',
    frameworks: ['cmmc_l2', 'nist_800_171'],
    cuiBoundary: [],
    sspControls: [
      {
        controlId: 'AC.L1-3.1.1',
        framework: 'cmmc_l2',
        family: 'Access Control',
        title: 'Limit System Access',
        description: 'Limit access to authorized users',
        status: 'fully_implemented',
        implementationDescription: 'Implemented RBAC',
        evidenceIds: ['ev-001'],
        responsibleParty: 'Security Team',
        lastAssessed: FIXED_TS,
        nextAssessment: '2027-06-30T00:00:00.000Z',
      },
    ],
    poamItems: [],
    supplierRisk: [],
    aiInventory: [],
    sbom: [
      { componentName: 'nginx', version: '1.25', supplier: 'nginx inc', license: 'BSD', cveOpen: 0, cveCritical: 0, lastScanned: FIXED_TS },
    ],
    aiBom: [],
    sprsScore: 0,
    agentReceipts: [],
    exportFormats: ['json', 'pdf'],
    ...overrides,
  };
}

// ===========================================================================
// 1. Trust Transaction + Evidence Graph Integration
// ===========================================================================

describe('Trust Transaction + Evidence Graph Integration', () => {
  it('creates a trust transaction and writes it to the evidence graph as a node', () => {
    const tx = createTrustTransaction(baseTxInput());
    const graphNode = nodeObject({
      orgSlug: tx.orgSlug,
      graphId: `trust_txn:${tx.transactionId}`,
      objectType: 'evidence',
      label: `Trust Transaction ${tx.transactionId}`,
      source: 'trust-transaction',
      framework: 'CMMC',
      controlIds: tx.evidence?.controlIds ?? [],
      weight: 90,
    });

    assert.equal(graphNode.objectKind, 'node');
    assert.ok(graphNode.objectHash.length === 64);
    assert.equal(graphNode.source, 'trust-transaction');
  });

  it('verifies the graph node hash matches recomputed hash', () => {
    const tx = createTrustTransaction(baseTxInput());
    const graphNode = nodeObject({
      orgSlug: tx.orgSlug,
      graphId: `trust_txn:${tx.transactionId}`,
      objectType: 'evidence',
      label: `Trust Transaction ${tx.transactionId}`,
      source: 'trust-transaction',
      framework: 'CMMC',
      controlIds: tx.evidence?.controlIds ?? [],
      weight: 90,
    });

    const recomputed = evidenceObjectHash({
      orgSlug: graphNode.orgSlug,
      graphId: graphNode.graphId,
      objectKind: graphNode.objectKind,
      objectType: graphNode.objectType,
      label: graphNode.label,
      source: graphNode.source,
    });
    assert.equal(graphNode.objectHash, recomputed);
  });

  it('snapshot includes trust transaction node with org ownership edge', () => {
    const tx = createTrustTransaction(baseTxInput());
    const graphNode = nodeObject({
      orgSlug: tx.orgSlug,
      graphId: `trust_txn:${tx.transactionId}`,
      objectType: 'evidence',
      label: `Trust Transaction ${tx.transactionId}`,
      source: 'trust-transaction',
      framework: 'CMMC',
      controlIds: tx.evidence?.controlIds ?? [],
      weight: 90,
    });

    const snapshot = objectsToSnapshot({ orgSlug: tx.orgSlug, objects: [graphNode] });
    assert.equal(snapshot.ok, true);

    const txnNode = snapshot.nodes.find((n) => n.id === graphNode.graphId);
    assert.ok(txnNode, 'Trust transaction node exists in snapshot');

    const ownsEdge = snapshot.edges.find(
      (e) => e.type === 'owns' && e.to === graphNode.graphId,
    );
    assert.ok(ownsEdge, 'Org owns the trust transaction node');
  });

  it('tx hash and graph object hash are independently verifiable', () => {
    const tx = createTrustTransaction(baseTxInput());
    const txHash = hashTrustTransaction(tx);
    assert.equal(tx.transactionHash, txHash);

    const graphNode = nodeObject({
      orgSlug: tx.orgSlug,
      graphId: `trust_txn:${tx.transactionId}`,
      objectType: 'evidence',
      label: `Trust Transaction ${tx.transactionId}`,
      source: 'trust-transaction',
      framework: 'CMMC',
      controlIds: tx.evidence?.controlIds ?? [],
      weight: 90,
    });

    const txVerify = verifyTrustTransaction(tx);
    assert.equal(txVerify.ok, true);

    const graphRecompute = evidenceObjectHash({
      orgSlug: graphNode.orgSlug,
      graphId: graphNode.graphId,
      objectKind: graphNode.objectKind,
      objectType: graphNode.objectType,
      label: graphNode.label,
      source: graphNode.source,
    });
    assert.equal(graphNode.objectHash, graphRecompute);
  });

  it('tampered graph node is detectable via hash mismatch', () => {
    const tx = createTrustTransaction(baseTxInput());
    const graphNode = nodeObject({
      orgSlug: tx.orgSlug,
      graphId: `trust_txn:${tx.transactionId}`,
      objectType: 'evidence',
      label: `Trust Transaction ${tx.transactionId}`,
      source: 'trust-transaction',
      framework: 'CMMC',
      controlIds: tx.evidence?.controlIds ?? [],
      weight: 90,
    });

    const tamperedHash = evidenceObjectHash({
      orgSlug: graphNode.orgSlug,
      graphId: graphNode.graphId,
      objectKind: graphNode.objectKind,
      objectType: graphNode.objectType,
      label: 'Tampered Label',
      source: graphNode.source,
    });

    assert.notEqual(graphNode.objectHash, tamperedHash, 'Tampered label produces different hash');
  });
});

// ===========================================================================
// 2. Agent Policy Firewall + Trust Transaction Integration
// ===========================================================================

describe('Agent Policy Firewall + Trust Transaction Integration', () => {
  let firewall: AgentPolicyFirewall;

  beforeEach(() => {
    firewall = new AgentPolicyFirewall();
  });

  it('evaluates an action through the firewall and creates a matching trust transaction', () => {
    const actor = makeActor();
    const request = makeRequest();
    const context = makeContext();

    const decision = firewall.evaluate(actor, request, context);
    assert.equal(decision.allowed, true);

    const receipt = firewall.createReceipt(actor, request, context, decision);
    const formattedReceipt = formatFirewallReceiptForEvidenceGraph(receipt);

    const tx = createTrustTransaction({
      kind: 'agent_intent',
      status: 'approved',
      tenantId: actor.tenantId,
      orgSlug: actor.orgSlug,
      actor: { id: actor.id, type: actor.type, tenantId: actor.tenantId, did: `did:grc:${actor.id}` },
      action: {
        name: request.toolName,
        tool: request.toolName,
        idempotencyKey: request.idempotencyKey,
      },
      policy: {
        policyId: 'agent-policy-firewall/default',
        decision: decision.allowed ? 'allow' : 'deny',
        sandboxPolicy: context.sandboxPolicy,
        approvalThreshold: context.approvalThreshold,
        replayWindowSeconds: context.replayWindowSeconds,
      },
      dataBoundary: context.dataBoundary,
      evidence: {
        graphId: formattedReceipt.graphId,
        graphObjectHash: formattedReceipt.objectHash,
        controlIds: context.controlImpactIds,
        frameworkCodes: ['CMMC'],
      },
      exportTargets: ['evidence_graph'],
      createdAt: FIXED_TS,
    });

    assert.equal(tx.policy?.decision, 'allow');
    assert.equal(tx.tenantId, actor.tenantId);
    assert.equal(tx.actor.id, actor.id);
    assert.ok(verifyTrustTransaction(tx).ok, 'Trust transaction from firewall receipt is valid');
  });

  it('firewall receipt hash matches formatted evidence graph hash', () => {
    const actor = makeActor();
    const request = makeRequest();
    const context = makeContext();

    const decision = firewall.evaluate(actor, request, context);
    const receipt = firewall.createReceipt(actor, request, context, decision);
    const formatted = formatFirewallReceiptForEvidenceGraph(receipt);

    assert.equal(formatted.objectHash.length, 64);
    assert.equal(formatted.objectKind, 'node');
    assert.equal(formatted.objectType, 'policy_decision');
    assert.equal(formatted.source, 'agent-policy-firewall');
  });

  it('denied action produces trust transaction with denied policy decision', () => {
    const actor = makeActor();
    const request = makeRequest({ toolName: 'admin.drop_table' });
    const context = makeContext({ allowedTools: [] });

    const decision = firewall.evaluate(actor, request, context);
    assert.equal(decision.allowed, false);

    const receipt = firewall.createReceipt(actor, request, context, decision);

    const tx = createTrustTransaction({
      kind: 'agent_intent',
      status: 'denied',
      tenantId: actor.tenantId,
      orgSlug: actor.orgSlug,
      actor: { id: actor.id, type: actor.type, tenantId: actor.tenantId, did: `did:grc:${actor.id}` },
      action: {
        name: request.toolName,
        tool: request.toolName,
        idempotencyKey: request.idempotencyKey,
      },
      policy: {
        policyId: 'agent-policy-firewall/default',
        decision: 'deny',
        sandboxPolicy: context.sandboxPolicy,
        approvalThreshold: context.approvalThreshold,
        replayWindowSeconds: context.replayWindowSeconds,
      },
      dataBoundary: context.dataBoundary,
      evidence: {
        graphId: `fw_receipt:${receipt.receiptId}`,
        graphObjectHash: receipt.receiptHash,
        controlIds: [],
        frameworkCodes: [],
      },
      exportTargets: [],
      createdAt: FIXED_TS,
    });

    assert.equal(tx.status, 'denied');
    assert.equal(tx.policy?.decision, 'deny');
    assert.ok(verifyTrustTransaction(tx).ok);
  });

  it('replay detection blocks second trust transaction creation', () => {
    const actor = makeActor();
    const request = makeRequest({ idempotencyKey: 'replay-integration-001' });
    const context = makeContext();

    const decision1 = firewall.evaluate(actor, request, context);
    assert.equal(decision1.allowed, true);
    assert.equal(decision1.replayDetected, false);

    const decision2 = firewall.evaluate(actor, request, context);
    assert.equal(decision2.allowed, false);
    assert.equal(decision2.reason, 'replay_detected');
  });

  it('blast radius check gates trust transaction creation', () => {
    const fw = new AgentPolicyFirewall({ maxBlastRadius: 3 });
    const actor = makeActor();
    const request = makeRequest({ tier: 'destructive', toolName: 'db.drop' });
    const context = makeContext({
      controlImpactIds: ['c1', 'c2', 'c3', 'c4'],
      allowedTools: [],
    });

    const decision = fw.evaluate(actor, request, context);
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'blast_radius_exceeded');
  });
});

// ===========================================================================
// 3. Verifier Network + Defense Procurement Integration
// ===========================================================================

describe('Verifier Network + Defense Procurement Integration', () => {
  let room: VerifierRoom;
  let packet: ReturnType<typeof buildProcurementPacket>;

  beforeEach(() => {
    room = createVerifierRoom({
      tenantId: 1,
      orgSlug: 'acme-corp',
      scope: 'auditor',
      verifiers: [makeVerifier()],
      exposedControlIds: ['AC.L1-3.1.1', 'AC.L1-3.1.2'],
      exposedEvidenceIds: ['ev-001', 'ev-002'],
      exposedFrameworks: ['CMMC'],
      exposedGraphPaths: ['graph:root', 'graph:controls'],
      packetMode: 'auditor',
    });
    packet = buildProcurementPacket(minimalPacket());
  });

  it('creates verifier room and procurement packet with compatible IDs', () => {
    assert.ok(room.roomId.startsWith('vroom:'));
    assert.ok(packet.packetId.startsWith('procurement:'));
  });

  it('links procurement packet to verifier room via export packet', () => {
    const exportPkt = buildVerifierExportPacket({
      roomId: room.roomId,
      exportedBy: 'ver-001',
      format: 'json',
      graphPaths: room.exposedGraphPaths,
      evidenceHashes: ['hash:ev-001', 'hash:ev-002'],
      controlIds: room.exposedControlIds,
      redacted: true,
    });

    assert.ok(exportPkt.packetId.startsWith('vexport:'));
    assert.equal(exportPkt.format, 'json');
    assert.equal(exportPkt.redacted, true);
    assert.ok(exportPkt.packetHash.length === 64);
  });

  it('verifier can access room and export procurement data', () => {
    const access = verifyRoomAccess(room, 'ver-001');
    assert.equal(access.allowed, true);

    const exportPkt = buildVerifierExportPacket({
      roomId: room.roomId,
      exportedBy: 'ver-001',
      format: 'json',
      graphPaths: ['graph:root'],
      evidenceHashes: ['hash:ev-001'],
      controlIds: room.exposedControlIds,
      redacted: false,
    });

    assert.equal(exportPkt.redacted, false);
    assert.ok(verifyProcurementPacket(packet).ok);
  });

  it('unregistered verifier cannot access procurement-linked room', () => {
    const access = verifyRoomAccess(room, 'ver-unknown');
    assert.equal(access.allowed, false);
    assert.equal(access.reason, 'verifier_not_in_room');
  });

  it('verifier event records review of procurement evidence', () => {
    const event = createVerifierEvent({
      roomId: room.roomId,
      verifierId: 'ver-001',
      action: 'review',
      targetType: 'evidence',
      targetId: 'ev-001',
      details: 'Reviewed procurement evidence for control AC.L1-3.1.1',
    });

    assert.ok(event.eventId.startsWith('vevt:'));
    assert.equal(event.roomId, room.roomId);
    assert.equal(event.action, 'review');
    assert.equal(event.receiptHash.length, 64);
  });

  it('procurement packet integrity is verifiable independently', () => {
    const result = verifyProcurementPacket(packet);
    assert.equal(result.ok, true);
    assert.equal(result.errors.length, 0);
  });

  it('tampered procurement packet fails verification', () => {
    const tampered = { ...packet, packetHash: '0'.repeat(64) };
    const result = verifyProcurementPacket(tampered);
    assert.equal(result.ok, false);
    assert.ok(result.errors.includes('packet_hash_mismatch'));
  });

  it('room and export packet both carry verifiable hashes', () => {
    assert.ok(room.roomHash.length === 64);
    const exportPkt = buildVerifierExportPacket({
      roomId: room.roomId,
      exportedBy: 'ver-001',
      format: 'pdf',
      graphPaths: ['graph:root'],
      evidenceHashes: [],
      controlIds: ['AC.L1-3.1.1'],
      redacted: true,
    });
    assert.ok(exportPkt.packetHash.length === 64);
  });
});

// ===========================================================================
// 4. Benchmark Intelligence + Trust Score Integration
// ===========================================================================

describe('Benchmark Intelligence + Trust Score Integration', () => {
  it('aggregates benchmark signals and feeds them into trust score calculation', async () => {
    const signals: BenchmarkSignal[] = [70, 80, 90, 85, 75].map((v) =>
      createBenchmarkSignal({
        tenantId: 1,
        orgSlug: 'acme-corp',
        category: 'evidence_freshness',
        scope: 'tenant',
        value: v,
        unit: 'percent',
        framework: 'SOC2',
        industry: 'tech',
      }),
    );

    const agg = aggregateBenchmarkSignals(signals, 'evidence_freshness', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });
    assert.equal(agg.sampleSize, 5);
    assert.ok(agg.statistics.mean >= 70 && agg.statistics.mean <= 90);

    const overall = computeOverallScore({
      evidence_freshness: agg.statistics.mean,
    });
    assert.ok(overall.score > 0);
    assert.ok(overall.percentile >= 1);
  });

  it('trust score engine produces a score derived from benchmark-derived compliance input', async () => {
    const engine = new AgentTrustScoreEngine({
      issuerId: 'did:grc:test',
      credentialStore: mockCredentialStore,
    });

    const benchSignals: BenchmarkSignal[] = [85, 90, 92, 88].map((v) =>
      createBenchmarkSignal({
        tenantId: 1,
        orgSlug: 'acme-corp',
        category: 'automation_success_rate',
        scope: 'tenant',
        value: v,
        unit: 'percent',
      }),
    );

    const agg = aggregateBenchmarkSignals(benchSignals, 'automation_success_rate', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });

    const overall = computeOverallScore({ automation_success_rate: agg.statistics.mean });
    const complianceScore = overall.score;

    const behavioralSignals: BehavioralSignal[] = [
      { type: 'normal_operation', timestamp: FIXED_TS, confidence: 0.9, details: 'Clean ops', impact: 0 },
      { type: 'normal_operation', timestamp: FIXED_TS, confidence: 0.85, details: 'Standard queries', impact: 0 },
    ];

    const profile = await engine.scoreAgent(
      'did:grc:bench-agent',
      'Benchmark Agent',
      'tenant-1',
      behavioralSignals,
      complianceScore,
    );

    assert.ok(profile.overallTrustScore >= 0);
    assert.ok(profile.overallTrustScore <= 100);
    assert.equal(profile.compliancePosture.overallScore, complianceScore);
  });

  it('multiple benchmark categories feed into a composite trust score', async () => {
    const freshnessAgg = aggregateBenchmarkSignals(
      [80, 85, 90].map((v) =>
        createBenchmarkSignal({ tenantId: 1, orgSlug: 'a', category: 'evidence_freshness', scope: 'tenant', value: v, unit: '%' }),
      ),
      'evidence_freshness',
      'tenant',
      { from: '2020-01-01T00:00:00.000Z', to: '2030-12-31T23:59:59.999Z' },
    );

    const mttrAgg = aggregateBenchmarkSignals(
      [24, 36, 48].map((v) =>
        createBenchmarkSignal({ tenantId: 1, orgSlug: 'a', category: 'mttr', scope: 'tenant', value: v, unit: 'hours' }),
      ),
      'mttr',
      'tenant',
      { from: '2020-01-01T00:00:00.000Z', to: '2030-12-31T23:59:59.999Z' },
    );

    const overall = computeOverallScore({
      evidence_freshness: freshnessAgg.statistics.mean,
      mttr: mttrAgg.statistics.mean,
    });

    assert.ok(overall.score > 0);
    assert.ok(overall.percentile >= 1);
    assert.ok(overall.percentile <= 99);
  });

  it('empty benchmark aggregation results in lower trust score', async () => {
    const agg = aggregateBenchmarkSignals([], 'evidence_freshness', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });
    assert.equal(agg.sampleSize, 0);

    const overall = computeOverallScore({ evidence_freshness: 0 });
    assert.ok(overall.score >= 0);
  });

  it('trust score engine reflects benchmark-derived compliance score', async () => {
    const engine = new AgentTrustScoreEngine({
      issuerId: 'did:grc:test',
      credentialStore: mockCredentialStore,
    });

    const highSignals: BenchmarkSignal[] = [95, 98, 97].map((v) =>
      createBenchmarkSignal({ tenantId: 1, orgSlug: 'a', category: 'evidence_freshness', scope: 'tenant', value: v, unit: '%' }),
    );
    const highAgg = aggregateBenchmarkSignals(highSignals, 'evidence_freshness', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });
    const highOverall = computeOverallScore({ evidence_freshness: highAgg.statistics.mean });

    const lowSignals: BenchmarkSignal[] = [20, 25, 30].map((v) =>
      createBenchmarkSignal({ tenantId: 1, orgSlug: 'b', category: 'evidence_freshness', scope: 'tenant', value: v, unit: '%' }),
    );
    const lowAgg = aggregateBenchmarkSignals(lowSignals, 'evidence_freshness', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });
    const lowOverall = computeOverallScore({ evidence_freshness: lowAgg.statistics.mean });

    const cleanSignals: BehavioralSignal[] = [
      { type: 'normal_operation', timestamp: FIXED_TS, confidence: 0.9, details: 'Normal', impact: 0 },
    ];

    const highProfile = await engine.scoreAgent('did:grc:high', 'High Agent', 't', cleanSignals, highOverall.score);
    const lowProfile = await engine.scoreAgent('did:grc:low', 'Low Agent', 't', cleanSignals, lowOverall.score);

    assert.ok(highProfile.overallTrustScore >= lowProfile.overallTrustScore,
      'Higher benchmark compliance should yield >= trust score');
  });
});

// ===========================================================================
// 5. Framework Crosswalk + Evidence Integration
// ===========================================================================

describe('Framework Crosswalk + Evidence Integration', () => {
  const crosswalk = new FrameworkCrosswalk();

  it('creates evidence for a control and finds equivalent controls via crosswalk', () => {
    const evidence = nodeObject({
      orgSlug: 'acme-corp',
      graphId: 'evidence:soc2:CC6.1',
      objectType: 'evidence',
      label: 'SOC2 CC6.1 Evidence',
      source: 'auto-evidence',
      framework: 'SOC2',
      controlIds: ['CC6.1'],
      weight: 90,
    });

    const equiv = crosswalk.findEquivalentControls('CC6.1');
    assert.ok(equiv.length > 0, 'Should find equivalent controls for CC6.1');

    const targetFrameworks = equiv.map((m) => m.targetFramework);
    assert.ok(targetFrameworks.length > 0);
  });

  it('evidence node satisfies multiple frameworks via crosswalk mappings', () => {
    const evidence = nodeObject({
      orgSlug: 'acme-corp',
      graphId: 'evidence:soc2:CC6.1',
      objectType: 'evidence',
      label: 'SOC2 CC6.1 Evidence',
      source: 'auto-evidence',
      framework: 'SOC2',
      controlIds: ['CC6.1'],
      weight: 90,
    });

    const mappings = crosswalk.getMappings('soc2', 'iso27001');
    assert.ok(mappings.length > 0, 'SOC2-ISO27001 mappings exist');

    const cc61Mapping = mappings.find((m) => m.sourceControl === 'CC6.1');
    assert.ok(cc61Mapping, 'CC6.1 has a mapping to ISO27001');
  });

  it('multi-framework coverage calculation includes evidence controls', () => {
    const controls = ['CC6.1', 'CC7.2'];
    const coverage = crosswalk.calculateMultiFrameworkCoverage(controls, ['soc2', 'iso27001']);
    assert.ok(coverage >= 0 && coverage <= 1);
  });

  it('crosswalk report shows gaps for controls without evidence', () => {
    const report = crosswalk.generateCrosswalk('soc2', 'iso27001');
    assert.equal(report.sourceFramework, 'soc2');
    assert.equal(report.targetFramework, 'iso27001');
    assert.ok(report.mappings.length > 0);
    assert.ok(report.coverage >= 0 && report.coverage <= 1);
    assert.ok(Array.isArray(report.gaps));
  });

  it('evidence graph snapshot includes evidence and control nodes with edges', () => {
    const evidenceNode = nodeObject({
      orgSlug: 'acme-corp',
      graphId: 'evidence:soc2:CC6.1',
      objectType: 'evidence',
      label: 'SOC2 CC6.1 Evidence',
      source: 'auto-evidence',
      framework: 'SOC2',
      controlIds: ['CC6.1'],
      weight: 90,
    });

    const provesEdge = edgeObject({
      orgSlug: 'acme-corp',
      graphId: 'edge:proves:CC6.1',
      objectType: 'proves',
      label: 'Evidence proves CC6.1',
      source: 'auto-evidence',
      fromId: evidenceNode.graphId,
      toId: 'control:CC6.1',
      confidence: 0.95,
    });

    const snapshot = objectsToSnapshot({
      orgSlug: 'acme-corp',
      objects: [evidenceNode, provesEdge],
    });

    assert.equal(snapshot.ok, true);
    assert.ok(snapshot.nodes.length >= 3);
    assert.ok(snapshot.edges.length >= 2);

    const ctrlNode = snapshot.nodes.find((n) => n.id === 'control:CC6.1');
    assert.ok(ctrlNode, 'Control CC6.1 node exists');
  });

  it('crosswalk identifies overlaps between frameworks', () => {
    const overlap = crosswalk.findOverlaps('soc2', 'iso27001');
    assert.equal(overlap.framework1, 'soc2');
    assert.equal(overlap.framework2, 'iso27001');
    assert.ok(overlap.overlappingControls >= 0);
    assert.ok(overlap.totalControls > 0);
  });

  it('evidence satisfies CMMC and NIST-800-171 via crosswalk', () => {
    const cmmcToNist = crosswalk.getMappings('cmmc', 'nist_800_171');
    assert.ok(cmmcToNist.length > 0, 'CMMC-NIST 800-171 mappings exist');

    const evidence = nodeObject({
      orgSlug: 'acme-corp',
      graphId: 'evidence:cmmc:AC.L1-3.1.1',
      objectType: 'evidence',
      label: 'CMMC AC.L1-3.1.1 Evidence',
      source: 'auto-evidence',
      framework: 'CMMC',
      controlIds: ['AC.L1-3.1.1'],
      weight: 85,
    });

    assert.equal(evidence.framework, 'CMMC');
    assert.deepEqual(evidence.controlIds, ['AC.L1-3.1.1']);
  });
});

// ===========================================================================
// 6. Full Pipeline: Scan -> Evidence -> Crosswalk -> Trust -> Verifier
// ===========================================================================

describe('Full Pipeline: Scan -> Evidence -> Crosswalk -> Trust -> Verifier', () => {
  it('simulates a complete compliance pipeline end-to-end', async () => {
    // --- Step 1: Simulate a compliance scan (firewall evaluates agent action) ---
    const firewall = new AgentPolicyFirewall();
    const actor = makeActor({ id: 'agent:compliance-scanner', role: 'executor' });
    const scanRequest = makeRequest({
      toolName: 'compliance.scan',
      tier: 'read',
      idempotencyKey: 'scan-001',
      args: { scanType: 'full', frameworks: ['CMMC', 'SOC2'] },
    });
    const scanContext = makeContext({ role: 'executor' });

    const scanDecision = firewall.evaluate(actor, scanRequest, scanContext);
    assert.equal(scanDecision.allowed, true, 'Scan action approved by firewall');

    const scanReceipt = firewall.createReceipt(actor, scanRequest, scanContext, scanDecision);
    const formattedReceipt = formatFirewallReceiptForEvidenceGraph(scanReceipt);

    // --- Step 2: Create evidence artifacts from scan results ---
    const evidenceNodes: EvidenceGraphObject[] = [
      nodeObject({
        orgSlug: 'acme-corp',
        graphId: 'evidence:cmmc:AC.L1-3.1.1',
        objectType: 'evidence',
        label: 'CMMC AC.L1-3.1.1 Access Control Evidence',
        source: 'compliance-scanner',
        framework: 'CMMC',
        controlIds: ['AC.L1-3.1.1'],
        weight: 85,
      }),
      nodeObject({
        orgSlug: 'acme-corp',
        graphId: 'evidence:soc2:CC6.1',
        objectType: 'evidence',
        label: 'SOC2 CC6.1 Logical Access Evidence',
        source: 'compliance-scanner',
        framework: 'SOC2',
        controlIds: ['CC6.1'],
        weight: 90,
      }),
      nodeObject({
        orgSlug: 'acme-corp',
        graphId: 'evidence:cmmc:AC.L1-3.1.2',
        objectType: 'evidence',
        label: 'CMMC AC.L1-3.1.2 Authentication Evidence',
        source: 'compliance-scanner',
        framework: 'CMMC',
        controlIds: ['AC.L1-3.1.2'],
        weight: 80,
      }),
    ];

    assert.equal(evidenceNodes.length, 3);
    for (const node of evidenceNodes) {
      assert.ok(node.objectHash.length === 64, `Evidence ${node.graphId} has valid hash`);
    }

    // --- Step 3: Map evidence to multiple frameworks via crosswalk ---
    const crosswalk = new FrameworkCrosswalk();
    const equivCC61 = crosswalk.findEquivalentControls('CC6.1');
    assert.ok(equivCC61.length > 0, 'CC6.1 has cross-framework equivalents');

    const multiCoverage = crosswalk.calculateMultiFrameworkCoverage(
      ['CC6.1', 'AC.L1-3.1.1'],
      ['soc2', 'cmmc'],
    );
    assert.ok(multiCoverage >= 0 && multiCoverage <= 1, 'Multi-framework coverage is bounded');

    const soc2Nist = crosswalk.getMappings('soc2', 'nist_csf');
    assert.ok(soc2Nist.length > 0, 'SOC2-NIST CSF mappings exist');

    // --- Step 4: Calculate trust score from benchmark and compliance data ---
    const benchSignals: BenchmarkSignal[] = [82, 88, 91, 85].map((v) =>
      createBenchmarkSignal({
        tenantId: 1,
        orgSlug: 'acme-corp',
        category: 'evidence_freshness',
        scope: 'tenant',
        value: v,
        unit: 'percent',
        framework: 'SOC2',
      }),
    );

    const agg = aggregateBenchmarkSignals(benchSignals, 'evidence_freshness', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });
    assert.equal(agg.sampleSize, 4);

    const benchOverall = computeOverallScore({
      evidence_freshness: agg.statistics.mean,
    });
    assert.ok(benchOverall.score > 0);

    const trustEngine = new AgentTrustScoreEngine({
      issuerId: 'did:grc:acme',
      credentialStore: mockCredentialStore,
    });

    const behavioralSignals: BehavioralSignal[] = [
      { type: 'normal_operation', timestamp: FIXED_TS, confidence: 0.9, details: 'Scan completed cleanly', impact: 0 },
      { type: 'normal_operation', timestamp: FIXED_TS, confidence: 0.88, details: 'No anomalies detected', impact: 0 },
    ];

    const trustProfile = await trustEngine.scoreAgent(
      'did:grc:compliance-scanner',
      'Compliance Scanner',
      'tenant-1',
      behavioralSignals,
      benchOverall.score,
    );

    assert.ok(trustProfile.overallTrustScore >= 0);
    assert.ok(trustProfile.overallTrustScore <= 100);
    assert.equal(trustProfile.status, 'active');

    // --- Step 5: Create verifier room for audit ---
    const room = createVerifierRoom({
      tenantId: 1,
      orgSlug: 'acme-corp',
      scope: 'auditor',
      verifiers: [makeVerifier()],
      exposedControlIds: ['AC.L1-3.1.1', 'AC.L1-3.1.2', 'CC6.1'],
      exposedEvidenceIds: evidenceNodes.map((n) => n.graphId),
      exposedFrameworks: ['CMMC', 'SOC2'],
      exposedGraphPaths: ['graph:evidence', 'graph:controls', 'graph:scan-results'],
      packetMode: 'auditor',
    });

    assert.ok(room.roomId.startsWith('vroom:'));
    assert.equal(room.status, 'active');

    const access = verifyRoomAccess(room, 'ver-001');
    assert.equal(access.allowed, true);

    // --- Step 6: Create trust transaction linking everything ---
    const tx = createTrustTransaction({
      kind: 'agent_intent',
      status: 'approved',
      tenantId: 1,
      orgSlug: 'acme-corp',
      actor: { id: actor.id, type: actor.type, tenantId: 1, did: `did:grc:${actor.id}` },
      action: {
        name: 'full_compliance_pipeline',
        tool: 'compliance.pipeline',
        idempotencyKey: 'pipeline-001',
        correlationId: 'pipeline-run-001',
      },
      policy: {
        policyId: 'agent-policy-firewall/default',
        decision: 'allow',
        sandboxPolicy: scanContext.sandboxPolicy,
        approvalThreshold: scanContext.approvalThreshold,
        replayWindowSeconds: scanContext.replayWindowSeconds,
      },
      dataBoundary: 'tenant-confidential',
      evidence: {
        graphId: room.roomId,
        graphObjectHash: room.roomHash,
        controlIds: ['AC.L1-3.1.1', 'AC.L1-3.1.2', 'CC6.1'],
        frameworkCodes: ['CMMC', 'SOC2', 'NIST-CSF'],
      },
      exportTargets: ['evidence_graph', 'verifier_room'],
      createdAt: FIXED_TS,
    });

    const txVerify = verifyTrustTransaction(tx);
    assert.equal(txVerify.ok, true, 'Pipeline trust transaction is valid');

    // --- Step 7: Export verification packet ---
    const exportPkt = buildVerifierExportPacket({
      roomId: room.roomId,
      exportedBy: 'ver-001',
      format: 'pdf',
      graphPaths: room.exposedGraphPaths,
      evidenceHashes: evidenceNodes.map((n) => n.objectHash),
      controlIds: room.exposedControlIds,
      redacted: true,
    });

    assert.ok(exportPkt.packetId.startsWith('vexport:'));
    assert.equal(exportPkt.format, 'pdf');
    assert.equal(exportPkt.redacted, true);
    assert.ok(exportPkt.packetHash.length === 64);

    // --- Step 8: Build full evidence graph snapshot ---
    const snapshot = objectsToSnapshot({
      orgSlug: 'acme-corp',
      objects: [
        ...evidenceNodes,
        edgeObject({
          orgSlug: 'acme-corp',
          graphId: 'edge:scan:proves:CC6.1',
          objectType: 'proves',
          label: 'Scan evidence proves CC6.1',
          source: 'compliance-scanner',
          fromId: 'evidence:soc2:CC6.1',
          toId: 'control:CC6.1',
          confidence: 0.95,
        }),
        edgeObject({
          orgSlug: 'acme-corp',
          graphId: 'edge:scan:proves:AC.L1-3.1.1',
          objectType: 'proves',
          label: 'Scan evidence proves AC.L1-3.1.1',
          source: 'compliance-scanner',
          fromId: 'evidence:cmmc:AC.L1-3.1.1',
          toId: 'control:AC.L1-3.1.1',
          confidence: 0.92,
        }),
      ],
    });

    assert.equal(snapshot.ok, true);
    assert.ok(snapshot.nodes.length >= 5, 'Snapshot has evidence, control, and org nodes');
    assert.ok(snapshot.edges.length >= 3, 'Snapshot has owns and proves edges');

    // --- Final assertions: cross-component integrity ---
    assert.equal(tx.evidence?.graphId, room.roomId, 'Trust tx references verifier room');
    assert.equal(tx.evidence?.graphObjectHash, room.roomHash, 'Trust tx hash matches room hash');
    assert.equal(tx.policy?.decision, 'allow', 'Full pipeline approved');
    assert.ok(tx.transactionHash.length === 64, 'Trust tx has valid hash');
    assert.ok(exportPkt.packetHash.length === 64, 'Export packet has valid hash');
  });
});
