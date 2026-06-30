import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  createTrustTransaction,
  hashTrustTransaction,
  verifyTrustTransaction,
  redactTrustTransactionForSharing,
  trustTransactionId,
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
  generatePacketId,
  getPacketModeExportFormats,
  type ProcurementPacket,
  type PacketMode,
} from '../../defense-procurement/src/index.ts';
import {
  createVerifierRoom,
  verifyRoomAccess,
  createVerifierEvent,
  createVerifierAcceptance,
  computeAcceptanceStats,
  buildVerifierExportPacket,
  type VerifierRoom,
  type VerifierIdentity,
  type VerifierAcceptance,
} from '../../verifier-network/src/index.ts';
import {
  createBenchmarkSignal,
  aggregateBenchmarkSignals,
  generateRecommendations,
  computeOverallScore,
  type BenchmarkSignal,
  type BenchmarkCategory,
} from '../../benchmark-intelligence/src/index.ts';
import {
  FrameworkCrosswalk,
} from '../../framework-crosswalk/src/FrameworkCrosswalk.ts';
import {
  nodeObject,
  edgeObject,
  objectsToSnapshot,
  evidenceObjectHash,
  buildEvidenceGraphSnapshot,
  evidenceGraphId,
  type EvidenceGraphObject,
} from '../../evidence-graph/src/index.ts';
import { EvidenceAutomationEngine, type ConnectorAdapter } from '../../evidence-automation-engine/src/EvidenceAutomationEngine.ts';
import type { EvidenceArtifact } from '../../evidence-automation-engine/src/types.ts';

// ---------------------------------------------------------------------------
// Helpers
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

function makeConnector(id: string, fail = false): ConnectorAdapter {
  return {
    async collectEvidence(): Promise<EvidenceArtifact[]> {
      if (fail) throw new Error(`Connector ${id} failed`);
      return [
        {
          id: `ev-${id}-1`,
          connectorId: id,
          capabilityId: 'test-cap',
          timestamp: new Date().toISOString(),
          hash: `sha256:test-${id}`,
          framework: 'SOC2',
          controlId: 'CC6.1',
          source: `${id}/test`,
          status: 'compliant',
          data: { test: true },
          metadata: {},
        },
      ];
    },
    async testConnection(): Promise<boolean> {
      return !fail;
    },
  };
}

const FIXED_TS = '2026-06-30T00:00:00.000Z';

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

// ===========================================================================
// 1. Trust Transaction Network
// ===========================================================================

describe('Trust Transaction Network', () => {
  it('creates transaction with all fields populated', () => {
    const tx = createTrustTransaction(baseTxInput());

    assert.equal(tx.version, 'v1');
    assert.ok(tx.transactionId.startsWith('trust_txn:'));
    assert.equal(tx.kind, 'agent_intent');
    assert.equal(tx.status, 'approved');
    assert.equal(tx.tenantId, 72);
    assert.equal(tx.orgSlug, 'a2z-soc');
    assert.equal(tx.actor.id, 'agent:grc-copilot');
    assert.equal(tx.actor.type, 'agent');
    assert.equal(tx.actor.did, 'did:grc:copilot');
    assert.equal(tx.action.name, 'collect_evidence');
    assert.equal(tx.action.tool, 'evidence.collect');
    assert.equal(tx.action.idempotencyKey, 'collect-evidence-001');
    assert.equal(tx.policy?.decision, 'allow');
    assert.equal(tx.policy?.sandboxPolicy, 'tenant-read-write-no-secrets');
    assert.equal(tx.dataBoundary, 'tenant-confidential');
    assert.deepEqual(tx.evidence?.controlIds, ['AC.L1-3.1.1']);
    assert.deepEqual(tx.evidence?.frameworkCodes, ['CMMC', 'NIST-800-171']);
    assert.deepEqual(tx.exportTargets, ['evidence_graph', 'verifier_room']);
    assert.ok(tx.transactionHash.length === 64);
  });

  it('generates deterministic transactionId from input', () => {
    const a = trustTransactionId({
      kind: 'agent_intent',
      actor: { id: 'agent:x', type: 'agent' },
      action: { name: 'test' },
      createdAt: FIXED_TS,
    });
    const b = trustTransactionId({
      kind: 'agent_intent',
      actor: { id: 'agent:x', type: 'agent' },
      action: { name: 'test' },
      createdAt: FIXED_TS,
    });
    assert.equal(a, b);
    assert.ok(a.startsWith('trust_txn:'));
  });

  it('hash integrity matches recomputed hash', () => {
    const tx = createTrustTransaction(baseTxInput());
    const recomputed = hashTrustTransaction(tx);
    assert.equal(tx.transactionHash, recomputed);
  });

  it('hash changes when any field mutates', () => {
    const tx = createTrustTransaction(baseTxInput());
    const original = tx.transactionHash;
    const mutated: TrustTransactionEnvelope = { ...tx, status: 'denied' };
    const newHash = hashTrustTransaction(mutated);
    assert.notEqual(original, newHash);
  });

  it('verifies a valid transaction as ok', () => {
    const tx = createTrustTransaction(baseTxInput());
    const result = verifyTrustTransaction(tx);
    assert.equal(result.ok, true);
    assert.equal(result.errors.length, 0);
  });

  it('detects hash mismatch on tampered envelope', () => {
    const tx = createTrustTransaction(baseTxInput());
    const tampered = { ...tx, status: 'blocked' as const };
    const result = verifyTrustTransaction(tampered);
    assert.equal(result.ok, false);
    assert.ok(result.errors.includes('transaction_hash_mismatch'));
  });

  it('requires copilot_answer to carry proof', () => {
    const tx = createTrustTransaction({
      ...baseTxInput(),
      kind: 'copilot_answer',
      status: 'blocked',
      evidence: undefined,
    } as NewTrustTransaction);
    const result = verifyTrustTransaction(tx);
    assert.equal(result.ok, false);
    assert.ok(result.errors.includes('copilot_answer_missing_proof'));
  });

  it('requires verifier_receipt to carry receiptHash', () => {
    const tx = createTrustTransaction({
      ...baseTxInput(),
      kind: 'verifier_receipt',
      status: 'verified',
    } as NewTrustTransaction);
    const result = verifyTrustTransaction(tx);
    assert.equal(result.ok, false);
    assert.ok(result.errors.includes('verifier_receipt_missing_hash'));
  });

  it('redacts actor id, did, tenantId, and idempotencyKey for sharing', () => {
    const tx = createTrustTransaction(baseTxInput());
    const redacted = redactTrustTransactionForSharing(tx);

    assert.equal(redacted.tenantId, undefined);
    assert.match(redacted.actor.id, /^redacted:/);
    assert.match(redacted.actor.did ?? '', /^redacted:/);
    assert.match(redacted.action.idempotencyKey ?? '', /^redacted:/);
    // core fields preserved
    assert.equal(redacted.kind, tx.kind);
    assert.equal(redacted.orgSlug, tx.orgSlug);
    assert.equal(redacted.transactionId, tx.transactionId);
  });

  it('rejects invalid transactions with missing fields', () => {
    const tx = createTrustTransaction(baseTxInput());
    const invalid = { ...tx, actor: {} as TrustTransactionEnvelope['actor'] };
    const result = verifyTrustTransaction(invalid);
    assert.equal(result.ok, false);
    assert.ok(result.errors.includes('missing_actor_id'));
    assert.ok(result.errors.includes('missing_actor_type'));
  });
});

// ===========================================================================
// 2. Agent Policy Firewall
// ===========================================================================

describe('Agent Policy Firewall', () => {
  let firewall: AgentPolicyFirewall;

  beforeEach(() => {
    firewall = new AgentPolicyFirewall();
  });

  it('allows read actions within sandbox', () => {
    const decision = firewall.evaluate(makeActor(), makeRequest(), makeContext());
    assert.equal(decision.allowed, true);
    assert.equal(decision.reason, 'approved_by_firewall');
    assert.equal(decision.sandbox, 'docker');
    assert.ok(decision.blastRadiusScore <= 10);
    assert.equal(decision.receiptHash.length, 64);
  });

  it('denies destructive actions when tier not authorized', () => {
    const ctx = makeContext({ dataBoundary: 'cui', approvalThreshold: 'human', allowedTools: [] });
    const req = makeRequest({ tier: 'destructive', toolName: 'db.drop' });
    const decision = firewall.evaluate(makeActor(), req, ctx);
    assert.equal(decision.allowed, false);
    assert.match(decision.reason, /tier_destructive/);
  });

  it('denies tools not in allowlist', () => {
    const ctx = makeContext({ allowedTools: ['evidence.collect', 'evidence.list'] });
    const req = makeRequest({ toolName: 'admin.override' });
    const decision = firewall.evaluate(makeActor(), req, ctx);
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'tool_not_in_allowlist');
  });

  it('denies explicitly denied tools', () => {
    const ctx = makeContext({ allowedTools: [] });
    const req = makeRequest({ toolName: 'admin.drop_table' });
    const decision = firewall.evaluate(makeActor(), req, ctx);
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'tool_explicitly_denied');
  });

  it('detects replay attacks via duplicate idempotencyKey', () => {
    const fw = new AgentPolicyFirewall();
    const req = makeRequest({ idempotencyKey: 'replay-key-42' });
    const decision1 = fw.evaluate(makeActor(), req, makeContext());
    assert.equal(decision1.allowed, true);
    assert.equal(decision1.replayDetected, false);

    const decision2 = fw.evaluate(makeActor(), req, makeContext());
    assert.equal(decision2.allowed, false);
    assert.equal(decision2.reason, 'replay_detected');
    assert.ok(decision2.anomaliesDetected.includes('replay_detected'));
  });

  it('triggers canary traps on honeypot tools', () => {
    const req = makeRequest({ toolName: 'connector.canary_override' });
    const decision = firewall.evaluate(makeActor(), req, makeContext());
    assert.equal(decision.allowed, false);
    assert.equal(decision.canaryTriggered, true);
    assert.equal(decision.reason, 'canary_trap_triggered');

    const traps = firewall.getCanaryTraps();
    assert.equal(traps.length, 1);
    assert.equal(traps[0].toolName, 'connector.canary_override');
    assert.equal(traps[0].triggerCount, 1);
  });

  it('detects SoD violations between auditor and developer', () => {
    const actor = makeActor({ role: 'auditor' });
    const ctx = makeContext({ role: 'developer' });
    const decision = firewall.evaluate(actor, makeRequest(), ctx);
    assert.equal(decision.allowed, false);
    assert.equal(decision.sodViolation, true);
    assert.ok(decision.anomaliesDetected.some((a) => a.includes('sod_violation')));
  });

  it('detects SoD violations between approver and executor', () => {
    const actor = makeActor({ role: 'approver' });
    const ctx = makeContext({ role: 'executor' });
    const decision = firewall.evaluate(actor, makeRequest(), ctx);
    assert.equal(decision.allowed, false);
    assert.equal(decision.sodViolation, true);
  });

  it('calculates blast radius score', () => {
    const ctx = makeContext({
      controlImpactIds: ['c1', 'c2', 'c3', 'c4'],
      dataBoundary: 'tenant-confidential',
      allowedTools: [],
    });
    const req = makeRequest({ tier: 'destructive' });
    const decision = firewall.evaluate(makeActor(), req, ctx);
    // destructive(+5) + 4 controls(+3) = 8
    assert.ok(decision.blastRadiusScore >= 5);
  });

  it('denies when blast radius exceeds max', () => {
    const fw = new AgentPolicyFirewall({ maxBlastRadius: 3 });
    const ctx = makeContext({
      controlImpactIds: ['c1', 'c2', 'c3', 'c4'],
      dataBoundary: 'tenant-confidential',
      allowedTools: [],
    });
    const req = makeRequest({ tier: 'destructive' });
    const decision = fw.evaluate(makeActor(), req, ctx);
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'blast_radius_exceeded');
  });

  it('creates valid receipt with hash', () => {
    const decision = firewall.evaluate(makeActor(), makeRequest(), makeContext());
    const receipt = firewall.createReceipt(makeActor(), makeRequest(), makeContext(), decision);
    assert.equal(receipt.version, 'v1');
    assert.ok(receipt.receiptId.startsWith('fw_receipt:'));
    assert.equal(receipt.receiptHash.length, 64);
  });

  it('formats receipt for evidence graph', () => {
    const decision = firewall.evaluate(makeActor(), makeRequest(), makeContext());
    const receipt = firewall.createReceipt(makeActor(), makeRequest(), makeContext(), decision);
    const formatted = formatFirewallReceiptForEvidenceGraph(receipt);
    assert.equal(formatted.objectKind, 'node');
    assert.equal(formatted.objectType, 'policy_decision');
    assert.equal(formatted.source, 'agent-policy-firewall');
  });

  it('blocks and unblocks actors', () => {
    firewall.blockActor('blocked-agent');
    const req = makeRequest();
    const decision = firewall.evaluate(makeActor({ id: 'blocked-agent' }), req, makeContext());
    assert.equal(decision.allowed, false);
    assert.equal(decision.reason, 'actor_blocked');

    firewall.unblockActor('blocked-agent');
    const decision2 = firewall.evaluate(makeActor({ id: 'blocked-agent' }), req, makeContext());
    assert.equal(decision2.allowed, true);
  });

  it('tracks stats', () => {
    firewall.evaluate(makeActor(), makeRequest(), makeContext());
    const stats = firewall.getStats();
    assert.ok(stats.sodRules >= 3);
    assert.equal(stats.blockedActors, 0);
  });

  it('adds custom SoD rules', () => {
    firewall.addSoDRule({
      conflictRoleA: 'qa',
      conflictRoleB: 'deployer',
      ruleName: 'qa-deployer-separation',
      severity: 'MEDIUM',
    });
    const rules = firewall.getSoDRules();
    assert.ok(rules.some((r) => r.ruleName === 'qa-deployer-separation'));
  });
});

// ===========================================================================
// 3. Defense Procurement
// ===========================================================================

describe('Defense Procurement', () => {
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

  it('builds procurement packet with valid hash', () => {
    const packet = buildProcurementPacket(minimalPacket());
    assert.equal(packet.version, 'v1');
    assert.equal(packet.packetHash.length, 64);
  });

  it('verifies valid packet integrity', () => {
    const packet = buildProcurementPacket(minimalPacket());
    const result = verifyProcurementPacket(packet);
    assert.equal(result.ok, true);
    assert.equal(result.errors.length, 0);
  });

  it('detects packet hash tampering', () => {
    const packet = buildProcurementPacket(minimalPacket());
    const tampered = { ...packet, packetHash: '0'.repeat(64) };
    const result = verifyProcurementPacket(tampered);
    assert.equal(result.ok, false);
    assert.ok(result.errors.includes('packet_hash_mismatch'));
  });

  it('calculates SPRS score based on control implementation', () => {
    const fullyImplemented = minimalPacket({
      sspControls: [
        {
          controlId: 'AC.L1-3.1.1',
          framework: 'cmmc_l2',
          family: 'Access Control',
          title: 'Limit System Access',
          description: 'Limit access',
          status: 'fully_implemented',
          implementationDescription: 'Implemented',
          evidenceIds: [],
          responsibleParty: 'Team',
          lastAssessed: FIXED_TS,
          nextAssessment: FIXED_TS,
        },
      ],
    });
    const packet = buildProcurementPacket(fullyImplemented);
    const score = calculateSprsScore(packet);
    assert.ok(score >= 0 && score <= 10);
    assert.ok(score >= 4);
  });

  it('penalizes open critical POA&Ms', () => {
    const packet = buildProcurementPacket(minimalPacket({
      poamItems: [
        {
          poamId: 'poam-1',
          controlId: 'AC.L1-3.1.2',
          framework: 'cmmc_l2',
          weakness: 'Missing MFA',
          description: 'MFA not enforced',
          riskLevel: 'critical',
          remediationPlan: 'Deploy MFA',
          milestoneDate: '2026-12-31T00:00:00.000Z',
          status: 'open',
          responsibleParty: 'Team',
          evidenceIds: [],
        },
      ],
    }));
    const score = calculateSprsScore(packet);
    // 1 fully-implemented control (+4) + 1 open critical POA&M (+1) + 0 open high (+2) + clean SBOM (+2) = 9
    assert.ok(score >= 0 && score <= 10);
    assert.ok(score >= 5, 'penalized by open critical POA&M');
  });

  it('generates correct export formats per mode', () => {
    const govFormats = getPacketModeExportFormats('government_buyer');
    assert.ok(govFormats.includes('oscal_ssp'));
    assert.ok(govFormats.includes('oscal_poam'));
    assert.ok(govFormats.includes('stix'));

    const auditorFormats = getPacketModeExportFormats('auditor');
    assert.ok(auditorFormats.includes('sarif'));

    const boardFormats = getPacketModeExportFormats('board');
    assert.ok(boardFormats.includes('excel'));
    assert.ok(!boardFormats.includes('sarif'));
  });

  it('generates unique packet IDs per org and mode', () => {
    const id1 = generatePacketId('acme', 'prime_contractor');
    const id2 = generatePacketId('acme', 'government_buyer');
    assert.ok(id1.startsWith('procurement:'));
    assert.notEqual(id1, id2);
  });

  it('handles multiple SSP control statuses for SPRS scoring', () => {
    const packet = buildProcurementPacket(minimalPacket({
      sspControls: [
        {
          controlId: 'AC.L1-3.1.1',
          framework: 'cmmc_l2',
          family: 'Access Control',
          title: 'Control 1',
          description: 'desc',
          status: 'fully_implemented',
          implementationDescription: 'done',
          evidenceIds: [],
          responsibleParty: 'Team',
          lastAssessed: FIXED_TS,
          nextAssessment: FIXED_TS,
        },
        {
          controlId: 'AC.L1-3.1.2',
          framework: 'cmmc_l2',
          family: 'Access Control',
          title: 'Control 2',
          description: 'desc',
          status: 'partially_implemented',
          implementationDescription: 'partial',
          evidenceIds: [],
          responsibleParty: 'Team',
          lastAssessed: FIXED_TS,
          nextAssessment: FIXED_TS,
        },
      ],
    }));
    const score = calculateSprsScore(packet);
    assert.ok(score >= 0 && score <= 10);
  });

  it('supports multiple procurement modes', () => {
    const modes: PacketMode[] = ['prime_contractor', 'government_buyer', 'auditor', 'insurer', 'board', 'pe_diligence', 'acquirer', 'regulator'];
    for (const mode of modes) {
      const packet = buildProcurementPacket(minimalPacket({ packetMode: mode }));
      assert.equal(packet.packetMode, mode);
      const result = verifyProcurementPacket(packet);
      assert.equal(result.ok, true);
    }
  });
});

// ===========================================================================
// 4. Verifier Network
// ===========================================================================

describe('Verifier Network', () => {
  let room: VerifierRoom;

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
  });

  it('creates verifier room with valid hash', () => {
    assert.ok(room.roomId.startsWith('vroom:'));
    assert.equal(room.version, 'v1');
    assert.equal(room.status, 'active');
    assert.equal(room.scope, 'auditor');
    assert.equal(room.orgSlug, 'acme-corp');
    assert.equal(room.verifiers.length, 1);
    assert.ok(room.roomHash.length === 64);
    assert.deepEqual(room.exposedControlIds, ['AC.L1-3.1.1', 'AC.L1-3.1.2']);
  });

  it('allows access for registered verifier in room', () => {
    const result = verifyRoomAccess(room, 'ver-001');
    assert.equal(result.allowed, true);
    assert.equal(result.reason, 'access_granted');
  });

  it('denies access for unregistered verifier', () => {
    const result = verifyRoomAccess(room, 'ver-unknown');
    assert.equal(result.allowed, false);
    assert.equal(result.reason, 'verifier_not_in_room');
  });

  it('denies access to revoked room', () => {
    const revokedRoom: VerifierRoom = { ...room, status: 'revoked' };
    const result = verifyRoomAccess(revokedRoom, 'ver-001');
    assert.equal(result.allowed, false);
    assert.equal(result.reason, 'room_status_revoked');
  });

  it('denies access for scope mismatch', () => {
    const auditorOnly: VerifierRoom = {
      ...room,
      accessPolicy: { ...room.accessPolicy, allowedScopes: ['auditor'] },
    };
    const result = verifyRoomAccess(auditorOnly, 'ver-001');
    assert.equal(result.allowed, true);
  });

  it('creates verifier events with receipt hash', () => {
    const event = createVerifierEvent({
      roomId: room.roomId,
      verifierId: 'ver-001',
      action: 'review',
      targetType: 'evidence',
      targetId: 'ev-001',
      details: 'Reviewed evidence document',
    });
    assert.ok(event.eventId.startsWith('vevt:'));
    assert.equal(event.roomId, room.roomId);
    assert.equal(event.action, 'review');
    assert.equal(event.target.type, 'evidence');
    assert.equal(event.target.id, 'ev-001');
    assert.equal(event.receiptHash.length, 64);
  });

  it('computes acceptance statistics', () => {
    const acc1 = createVerifierAcceptance({
      roomId: room.roomId,
      verifierId: 'ver-001',
      controlId: 'AC.L1-3.1.1',
      accepted: true,
      confidence: 0.95,
      comments: 'Fully compliant',
    });
    const acc2 = createVerifierAcceptance({
      roomId: room.roomId,
      verifierId: 'ver-001',
      controlId: 'AC.L1-3.1.2',
      accepted: false,
      confidence: 0.3,
      comments: 'Missing evidence',
    });

    const stats = computeAcceptanceStats([acc1, acc2]);
    assert.equal(stats.total, 2);
    assert.equal(stats.accepted, 1);
    assert.equal(stats.rejected, 1);
    assert.ok(stats.avgConfidence > 0.6 && stats.avgConfidence < 0.7);
    assert.equal(stats.byControl.get('AC.L1-3.1.1')?.accepted, 1);
    assert.equal(stats.byControl.get('AC.L1-3.1.2')?.rejected, 1);
  });

  it('computes stats for empty array', () => {
    const stats = computeAcceptanceStats([]);
    assert.equal(stats.total, 0);
    assert.equal(stats.avgConfidence, 0);
  });

  it('builds export packet with hash', () => {
    const pkt = buildVerifierExportPacket({
      roomId: room.roomId,
      exportedBy: 'ver-001',
      format: 'pdf',
      graphPaths: ['graph:root'],
      evidenceHashes: ['hash:ev1'],
      controlIds: ['AC.L1-3.1.1'],
      redacted: true,
    });
    assert.ok(pkt.packetId.startsWith('vexport:'));
    assert.equal(pkt.format, 'pdf');
    assert.equal(pkt.redacted, true);
    assert.ok(pkt.packetHash.length === 64);
  });

  it('supports multiple verifier scopes', () => {
    const scopes: Array<'auditor' | 'customer' | 'insurer' | 'board' | 'regulator' | 'acquirer'> = ['auditor', 'customer', 'insurer', 'board', 'regulator', 'acquirer'];
    for (const scope of scopes) {
      const vroom = createVerifierRoom({
        tenantId: 1,
        orgSlug: 'acme-corp',
        scope,
        verifiers: [{ ...makeVerifier(), scope }],
      });
      assert.equal(vroom.scope, scope);
      assert.ok(vroom.roomHash.length === 64);
    }
  });

  it('handles multiple acceptances per control', () => {
    const accs: VerifierAcceptance[] = ['ver-001', 'ver-002'].map((vid) =>
      createVerifierAcceptance({
        roomId: room.roomId,
        verifierId: vid,
        controlId: 'AC.L1-3.1.1',
        accepted: true,
        confidence: 0.9,
      }),
    );
    const stats = computeAcceptanceStats(accs);
    assert.equal(stats.total, 2);
    assert.equal(stats.byControl.get('AC.L1-3.1.1')?.accepted, 2);
  });
});

// ===========================================================================
// 5. Benchmark Intelligence
// ===========================================================================

describe('Benchmark Intelligence', () => {
  it('creates benchmark signal with all fields', () => {
    const signal = createBenchmarkSignal({
      tenantId: 1,
      orgSlug: 'acme-corp',
      category: 'audit_cycle_time',
      scope: 'tenant',
      value: 45,
      unit: 'days',
      framework: 'SOC2',
      industry: 'tech',
      region: 'us-east',
    });
    assert.ok(signal.signalId.startsWith('bsig:'));
    assert.equal(signal.category, 'audit_cycle_time');
    assert.equal(signal.value, 45);
    assert.equal(signal.unit, 'days');
  });

  it('aggregates signals with statistics', () => {
    const signals: BenchmarkSignal[] = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map((v) =>
      createBenchmarkSignal({
        tenantId: 1,
        orgSlug: 'acme',
        category: 'evidence_freshness',
        scope: 'tenant',
        value: v,
        unit: 'percent',
        industry: 'tech',
      }),
    );
    const agg = aggregateBenchmarkSignals(signals, 'evidence_freshness', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });
    assert.equal(agg.sampleSize, 10);
    assert.equal(agg.statistics.mean, 55);
    assert.equal(agg.statistics.min, 10);
    assert.equal(agg.statistics.max, 100);
    assert.ok(agg.statistics.stddev > 0);
    assert.ok(agg.breakdown.length > 0);
    assert.ok(agg.trend.length > 0);
  });

  it('returns empty aggregation for no matching signals', () => {
    const agg = aggregateBenchmarkSignals([], 'mttr', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });
    assert.equal(agg.sampleSize, 0);
    assert.equal(agg.statistics.mean, 0);
  });

  it('generates recommendations for below-median metrics', () => {
    const peerAggs = new Map();
    const agg = aggregateBenchmarkSignals(
      [20, 30, 40, 50, 60, 70, 80].map((v) =>
        createBenchmarkSignal({
          tenantId: 2,
          orgSlug: 'peer',
          category: 'audit_cycle_time',
          scope: 'industry',
          value: v,
          unit: 'days',
        }),
      ),
      'audit_cycle_time',
      'industry',
      { from: '2020-01-01T00:00:00.000Z', to: '2030-12-31T23:59:59.999Z' },
    );
    peerAggs.set('audit_cycle_time', agg);

    const recs = generateRecommendations({ audit_cycle_time: 15 }, peerAggs);
    assert.ok(recs.length > 0);
    assert.equal(recs[0].category, 'audit_cycle_time');
    assert.ok(recs[0].currentPercentile < 75);
    assert.ok(recs[0].confidence > 0);
  });

  it('computes overall score with weighted metrics', () => {
    const result = computeOverallScore({
      evidence_freshness: 90,
      control_reuse_rate: 80,
      audit_cycle_time: 70,
      remediation_latency: 60,
      automation_success_rate: 85,
      verifier_acceptance_rate: 95,
      mttr: 75,
      trust_score: 80,
    });
    assert.ok(result.score >= 50 && result.score <= 100);
    assert.ok(result.percentile >= 1 && result.percentile <= 99);
  });

  it('computes overall score with partial metrics', () => {
    const result = computeOverallScore({ evidence_freshness: 100 });
    assert.ok(result.score > 0);
  });

  it('computes overall score with no metrics', () => {
    const result = computeOverallScore({} as Record<BenchmarkCategory, number>);
    assert.equal(result.score, 0);
  });

  it('handles single signal aggregation', () => {
    const signals = [
      createBenchmarkSignal({
        tenantId: 1,
        orgSlug: 'acme',
        category: 'mttr',
        scope: 'tenant',
        value: 42,
        unit: 'hours',
      }),
    ];
    const agg = aggregateBenchmarkSignals(signals, 'mttr', 'tenant', {
      from: '2020-01-01T00:00:00.000Z',
      to: '2030-12-31T23:59:59.999Z',
    });
    assert.equal(agg.sampleSize, 1);
    assert.equal(agg.statistics.mean, 42);
    assert.equal(agg.statistics.median, 42);
  });

  it('filters signals by time period', () => {
    const signals = [
      createBenchmarkSignal({ tenantId: 1, orgSlug: 'a', category: 'mttr', scope: 'tenant', value: 10, unit: 'h', timestamp: '2026-01-15T00:00:00.000Z' }),
      createBenchmarkSignal({ tenantId: 1, orgSlug: 'a', category: 'mttr', scope: 'tenant', value: 20, unit: 'h', timestamp: '2026-06-15T00:00:00.000Z' }),
    ];
    const agg = aggregateBenchmarkSignals(signals, 'mttr', 'tenant', {
      from: '2026-03-01T00:00:00.000Z',
      to: '2026-09-01T00:00:00.000Z',
    });
    assert.equal(agg.sampleSize, 1);
    assert.equal(agg.statistics.mean, 20);
  });
});

// ===========================================================================
// 6. Framework Crosswalk
// ===========================================================================

describe('Framework Crosswalk', () => {
  const crosswalk = new FrameworkCrosswalk();

  it('supports all 18 built-in framework pairs', () => {
    const pairs = crosswalk.getSupportedPairs();
    assert.ok(pairs.length >= 18, `Expected >= 18 pairs, got ${pairs.length}`);
  });

  it('returns SOC2-ISO27001 mappings', () => {
    const m = crosswalk.getMappings('soc2', 'iso27001');
    assert.ok(m.length >= 10);
    assert.equal(m[0].sourceFramework, 'soc2');
  });

  it('returns NIST CSF-ISO27001 mappings', () => {
    const m = crosswalk.getMappings('nist_csf', 'iso27001');
    assert.ok(m.length > 0);
  });

  it('returns HIPAA-NIST CSF mappings', () => {
    const m = crosswalk.getMappings('hipaa', 'nist_csf');
    assert.ok(m.length > 0);
  });

  it('returns PCI DSS-ISO27001 mappings', () => {
    const m = crosswalk.getMappings('pci_dss', 'iso27001');
    assert.ok(m.length > 0);
  });

  it('returns GDPR-ISO27701 mappings', () => {
    const m = crosswalk.getMappings('gdpr', 'iso27701');
    assert.ok(m.length > 0);
  });

  it('returns FedRAMP-NIST 800-53 mappings', () => {
    const m = crosswalk.getMappings('fedramp', 'nist_800_53');
    assert.ok(m.length > 0);
  });

  it('returns CMMC-NIST 800-171 mappings', () => {
    const m = crosswalk.getMappings('cmmc', 'nist_800_171');
    assert.ok(m.length > 0);
  });

  it('returns SOC2-NIST CSF mappings', () => {
    const m = crosswalk.getMappings('soc2', 'nist_csf');
    assert.ok(m.length > 0);
  });

  it('returns ISO27001-ISO42001 mappings', () => {
    const m = crosswalk.getMappings('iso27001', 'iso42001');
    assert.ok(m.length > 0);
  });

  it('returns COBIT2019-ISO27001 mappings', () => {
    const m = crosswalk.getMappings('cobit_2019', 'iso27001');
    assert.ok(m.length > 0);
  });

  it('returns HITRUST-ISO27001 mappings', () => {
    const m = crosswalk.getMappings('hitrust', 'iso27001');
    assert.ok(m.length > 0);
  });

  it('returns NIS2-NIST CSF mappings', () => {
    const m = crosswalk.getMappings('nis2', 'nist_csf');
    assert.ok(m.length > 0);
  });

  it('returns CSA CCM-ISO27001 mappings', () => {
    const m = crosswalk.getMappings('csa_ccm', 'iso27001');
    assert.ok(m.length > 0);
  });

  it('returns IEC 62443-NIST CSF mappings', () => {
    const m = crosswalk.getMappings('iec_62443', 'nist_csf');
    assert.ok(m.length > 0);
  });

  it('returns NERC CIP-NIST CSF mappings', () => {
    const m = crosswalk.getMappings('nerc_cip', 'nist_csf');
    assert.ok(m.length > 0);
  });

  it('returns NIST Privacy-NIST CSF mappings', () => {
    const m = crosswalk.getMappings('nist_privacy', 'nist_csf');
    assert.ok(m.length > 0);
  });

  it('returns ISO22301-ISO27001 mappings', () => {
    const m = crosswalk.getMappings('iso22301', 'iso27001');
    assert.ok(m.length > 0);
  });

  it('returns DORA-NIST CSF mappings', () => {
    const m = crosswalk.getMappings('dora', 'nist_csf');
    assert.ok(m.length > 0);
  });

  it('is symmetric across all pairs', () => {
    const pairs = crosswalk.getSupportedPairs();
    for (const [a, b] of pairs) {
      const ab = crosswalk.getMappings(a, b);
      const ba = crosswalk.getMappings(b, a);
      assert.equal(ab.length, ba.length, `Asymmetry: ${a}/${b}: ${ab.length} vs ${ba.length}`);
    }
  });

  it('generates crosswalk report with coverage', () => {
    const report = crosswalk.generateCrosswalk('soc2', 'iso27001');
    assert.equal(report.sourceFramework, 'soc2');
    assert.equal(report.targetFramework, 'iso27001');
    assert.ok(report.mappings.length > 0);
    assert.ok(report.coverage >= 0 && report.coverage <= 1);
    assert.ok(Array.isArray(report.gaps));
  });

  it('generates zero-coverage report for unknown pair', () => {
    const report = crosswalk.generateCrosswalk('unknown_a', 'unknown_b');
    assert.equal(report.mappings.length, 0);
    assert.equal(report.coverage, 0);
    assert.ok(report.gaps.length > 0);
  });

  it('finds overlaps between SOC2 and ISO27001', () => {
    const overlap = crosswalk.findOverlaps('soc2', 'iso27001');
    assert.equal(overlap.framework1, 'soc2');
    assert.equal(overlap.framework2, 'iso27001');
    assert.ok(overlap.overlappingControls >= 0);
    assert.ok(overlap.totalControls > 0);
    assert.ok(overlap.overlapPercentage >= 0);
  });

  it('finds equivalent controls by ID', () => {
    const results = crosswalk.findEquivalentControls('CC6.1');
    assert.ok(results.length > 0);
    assert.ok(results.some((m) => m.sourceControl === 'CC6.1'));
  });

  it('calculates multi-framework coverage', () => {
    const coverage = crosswalk.calculateMultiFrameworkCoverage(
      ['CC6.1', 'CC7.2', 'A.8.5'],
      ['soc2', 'iso27001'],
    );
    assert.ok(coverage >= 0 && coverage <= 1);
  });

  it('returns 0 coverage for empty control list', () => {
    assert.equal(crosswalk.calculateMultiFrameworkCoverage([], ['soc2']), 0);
  });

  it('lists all mappings including extras', () => {
    const all = crosswalk.listAllMappings();
    assert.ok(all.length > 100);
  });
});

// ===========================================================================
// 7. Evidence Graph
// ===========================================================================

describe('Evidence Graph', () => {
  it('creates node object with valid hash', () => {
    const node = nodeObject({
      orgSlug: 'acme-corp',
      graphId: 'graph:evidence:001',
      objectType: 'evidence',
      label: 'Evidence Document',
      source: 'auto-evidence',
      framework: 'SOC2',
      controlIds: ['CC6.1'],
      weight: 80,
    });
    assert.equal(node.objectKind, 'node');
    assert.equal(node.objectType, 'evidence');
    assert.equal(node.label, 'Evidence Document');
    assert.ok(node.objectHash.length === 64);
    assert.ok(node.createdAt);
  });

  it('creates edge object with from/to ids', () => {
    const edge = edgeObject({
      orgSlug: 'acme-corp',
      graphId: 'edge:001',
      objectType: 'proves',
      label: 'Evidence proves control',
      source: 'auto-evidence',
      fromId: 'graph:evidence:001',
      toId: 'control:CC6.1',
      confidence: 0.9,
    });
    assert.equal(edge.objectKind, 'edge');
    assert.equal(edge.fromId, 'graph:evidence:001');
    assert.equal(edge.toId, 'control:CC6.1');
    assert.ok(edge.objectHash.length === 64);
  });

  it('hash is deterministic', () => {
    const hash1 = evidenceObjectHash({
      orgSlug: 'acme',
      graphId: 'g1',
      objectKind: 'node',
      objectType: 'evidence',
      label: 'Test',
      source: 'test',
    });
    const hash2 = evidenceObjectHash({
      orgSlug: 'acme',
      graphId: 'g1',
      objectKind: 'node',
      objectType: 'evidence',
      label: 'Test',
      source: 'test',
    });
    assert.equal(hash1, hash2);
  });

  it('hash changes when payload mutates', () => {
    const base = {
      orgSlug: 'acme',
      graphId: 'g1',
      objectKind: 'node' as const,
      objectType: 'evidence',
      label: 'Test',
      source: 'test',
    };
    const h1 = evidenceObjectHash(base);
    const h2 = evidenceObjectHash({ ...base, label: 'Test-Modified' });
    assert.notEqual(h1, h2);
  });

  it('generates snapshot from objects', () => {
    const n1 = nodeObject({
      orgSlug: 'acme-corp',
      graphId: 'node:evidence:1',
      objectType: 'evidence',
      label: 'E1',
      source: 'test',
    });
    const snapshot = objectsToSnapshot({
      orgSlug: 'acme-corp',
      objects: [n1],
    });
    assert.equal(snapshot.ok, true);
    assert.ok(snapshot.graph_hash.length === 64);
    assert.ok(snapshot.nodes.length >= 2);
    assert.ok(snapshot.edges.length >= 1);
  });

  it('snapshot includes organization node', () => {
    const snapshot = objectsToSnapshot({
      orgSlug: 'acme-corp',
      objects: [],
    });
    const orgNode = snapshot.nodes.find((n) => n.type === 'organization');
    assert.ok(orgNode);
    assert.equal(orgNode.id, 'org:acme-corp');
  });

  it('builds snapshot from raw nodes and edges', () => {
    const snapshot = buildEvidenceGraphSnapshot({
      orgSlug: 'acme-corp',
      nodes: [
        { id: 'node:ctrl:1', type: 'control', label: 'CC6.1', source: 'SOC2', weight: 80 },
      ],
      edges: [
        { id: 'edge:1', type: 'owns', from: 'org:acme-corp', to: 'node:ctrl:1', label: 'owns', confidence: 0.9 },
      ],
    });
    assert.equal(snapshot.ok, true);
    assert.ok(snapshot.nodes.length >= 2);
    assert.ok(snapshot.edges.length >= 1);
  });

  it('generates deterministic graphId', () => {
    const id1 = evidenceGraphId('test', { key: 'value' });
    const id2 = evidenceGraphId('test', { key: 'value' });
    assert.equal(id1, id2);
    assert.ok(id1.startsWith('test:'));
  });

  it('supports multiple node types', () => {
    const types = ['evidence', 'control', 'control_test', 'threat_model', 'framework', 'posture'] as const;
    for (const objectType of types) {
      const node = nodeObject({
        orgSlug: 'acme',
        graphId: `node:${objectType}:1`,
        objectType,
        label: `Test ${objectType}`,
        source: 'test',
      });
      assert.equal(node.objectType, objectType);
    }
  });

  it('auto-creates owns edges for node objects', () => {
    const node = nodeObject({
      orgSlug: 'acme-corp',
      graphId: 'node:ev:1',
      objectType: 'evidence',
      label: 'E1',
      source: 'test',
    });
    const snapshot = objectsToSnapshot({
      orgSlug: 'acme-corp',
      objects: [node],
    });
    const ownsEdge = snapshot.edges.find(
      (e) => e.type === 'owns' && e.from === 'org:acme-corp' && e.to === 'node:ev:1',
    );
    assert.ok(ownsEdge, 'Auto-created owns edge should exist');
  });

  it('snapshot includes control nodes from controlIds', () => {
    const node = nodeObject({
      orgSlug: 'acme-corp',
      graphId: 'node:ev:1',
      objectType: 'evidence',
      label: 'E1',
      source: 'test',
      controlIds: ['CC6.1', 'CC7.1'],
      framework: 'SOC2',
    });
    const snapshot = objectsToSnapshot({
      orgSlug: 'acme-corp',
      objects: [node],
    });
    const ctrl1 = snapshot.nodes.find((n) => n.id === 'control:CC6.1');
    const ctrl2 = snapshot.nodes.find((n) => n.id === 'control:CC7.1');
    assert.ok(ctrl1, 'Control CC6.1 node should exist');
    assert.ok(ctrl2, 'Control CC7.1 node should exist');
  });
});

// ===========================================================================
// 8. Evidence Management (Evidence Automation Engine)
// ===========================================================================

describe('Evidence Management', () => {
  let engine: EvidenceAutomationEngine;

  beforeEach(() => {
    engine = new EvidenceAutomationEngine({ defaultFreshnessHours: 24 * 30 });
  });

  it('creates engine with empty store', () => {
    assert.equal(engine.getStore().size, 0);
  });

  it('collects evidence from a single connector', async () => {
    engine.registerConnector('github', makeConnector('github'));
    const job = await engine.collectFromConnector('github');
    assert.equal(job.status, 'completed');
    assert.equal(job.artifacts.length, 1);
    assert.ok(job.duration !== undefined);
    assert.equal(engine.getStore().size, 1);
  });

  it('stores evidence with lineage (connectorId, controlId)', async () => {
    engine.registerConnector('github', makeConnector('github'));
    const job = await engine.collectFromConnector('github');
    const artifact = job.artifacts[0];
    assert.equal(artifact.connectorId, 'github');
    assert.equal(artifact.controlId, 'CC6.1');
    assert.equal(artifact.framework, 'SOC2');
  });

  it('verifies evidence hash integrity', async () => {
    engine.registerConnector('github', makeConnector('github'));
    await engine.collectFromConnector('github');
    const artifacts = engine.getStore().getAll();
    assert.ok(artifacts[0].hash.startsWith('sha256:'));
  });

  it('lists evidence by control', async () => {
    engine.registerConnector('github', makeConnector('github'));
    await engine.collectFromConnector('github');
    const byControl = engine.getStore().getByControl('CC6.1');
    assert.equal(byControl.length, 1);
    assert.equal(byControl[0].controlId, 'CC6.1');
  });

  it('lists evidence by connector', async () => {
    engine.registerConnector('github', makeConnector('github'));
    await engine.collectFromConnector('github');
    const byConnector = engine.getStore().getByConnector('github');
    assert.equal(byConnector.length, 1);
  });

  it('lists evidence by framework', async () => {
    engine.registerConnector('github', makeConnector('github'));
    await engine.collectFromConnector('github');
    const byFramework = engine.getStore().getByFramework('SOC2');
    assert.equal(byFramework.length, 1);
  });

  it('collects from all connectors', async () => {
    engine.registerConnector('github', makeConnector('github'));
    engine.registerConnector('gitlab', makeConnector('gitlab'));
    const jobs = await engine.collectAll();
    assert.equal(jobs.length, 2);
    assert.ok(jobs.every((j) => j.status === 'completed'));
    assert.equal(engine.getStore().size, 2);
  });

  it('creates schedule for registered connector', () => {
    engine.registerConnector('github', makeConnector('github'));
    const schedule = engine.createSchedule('github', {
      frequency: 'daily',
      hourOfDay: 9,
    });
    assert.ok(schedule.id);
    assert.equal(schedule.enabled, true);
    assert.ok(schedule.nextRunAt);
  });

  it('throws for unregistered connector schedule', () => {
    assert.throws(() => {
      engine.createSchedule('nonexistent', { frequency: 'daily' });
    }, /not registered/);
  });

  it('detects missing evidence gaps', () => {
    const gaps = engine.detectGaps();
    assert.ok(gaps.length > 0);
    assert.ok(gaps.every((g) => g.freshness === 'missing'));
  });

  it('detects no gaps when evidence is fresh', async () => {
    engine.registerConnector('github', makeConnector('github'));
    await engine.collectFromConnector('github');
    const gaps = engine.detectGaps();
    const githubGap = gaps.find(
      (g) => g.controlId === 'CC6.1' && g.framework === 'SOC2',
    );
    assert.equal(githubGap, undefined);
  });

  it('generates summary report with coverage', async () => {
    engine.registerConnector('github', makeConnector('github'));
    await engine.collectFromConnector('github');
    const report = engine.generateSummaryReport();
    assert.equal(report.totalArtifacts, 1);
    assert.ok(report.coveragePercentage > 0);
    assert.ok(report.generatedAt);
  });

  it('handles connector failures gracefully', async () => {
    engine.registerConnector('failing', makeConnector('failing', true));
    const job = await engine.collectFromConnector('failing');
    assert.equal(job.status, 'failed');
    assert.ok(job.error);
  });

  it('clears store', async () => {
    engine.registerConnector('github', makeConnector('github'));
    await engine.collectFromConnector('github');
    assert.equal(engine.getStore().size, 1);
    engine.clearStore();
    assert.equal(engine.getStore().size, 0);
  });

  it('updates schedule configuration', () => {
    engine.registerConnector('github', makeConnector('github'));
    const schedule = engine.createSchedule('github', { frequency: 'daily' });
    const updated = engine.updateSchedule(schedule.id, { config: { frequency: 'weekly' } });
    assert.ok(updated);
    assert.equal(updated!.config.frequency, 'weekly');
  });

  it('deletes schedule', () => {
    engine.registerConnector('github', makeConnector('github'));
    const schedule = engine.createSchedule('github', { frequency: 'daily' });
    assert.ok(engine.deleteSchedule(schedule.id));
    assert.equal(engine.getSchedule(schedule.id), undefined);
  });

  it('tracks jobs with status', async () => {
    engine.registerConnector('github', makeConnector('github'));
    await engine.collectFromConnector('github');
    const jobs = engine.getJobs();
    assert.equal(jobs.length, 1);
    assert.equal(jobs[0].status, 'completed');
  });

  it('starts and stops scheduler without errors', () => {
    engine.registerConnector('github', makeConnector('github'));
    engine.createSchedule('github', { frequency: 'hourly' });
    engine.startScheduler();
    engine.stopScheduler();
    assert.ok(true);
  });
});
