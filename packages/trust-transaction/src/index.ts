import { createHash } from 'node:crypto';

export type TrustTransactionKind =
  | 'agent_intent'
  | 'policy_decision'
  | 'execution_result'
  | 'evidence_commit'
  | 'copilot_answer'
  | 'missing_evidence_task'
  | 'marketplace_pack'
  | 'verifier_receipt'
  | 'procurement_packet'
  | 'benchmark_signal';

export type TrustTransactionStatus =
  | 'proposed'
  | 'approved'
  | 'denied'
  | 'executed'
  | 'verified'
  | 'rejected'
  | 'blocked'
  | 'simulated';

export type TrustDataBoundary =
  | 'public'
  | 'tenant-confidential'
  | 'cui'
  | 'phi'
  | 'pci'
  | 'gdpr'
  | 'sovereign'
  | 'airgapped';

export interface TrustTransactionActor {
  id: string;
  type: 'human' | 'agent' | 'service' | 'verifier' | 'marketplace_pack';
  tenantId?: number;
  orgSlug?: string;
  role?: string;
  did?: string;
}

export interface TrustTransactionPolicy {
  policyId: string;
  decision: 'allow' | 'deny' | 'approval_required' | 'monitor_only';
  reason?: string;
  sandboxPolicy?: string;
  approvalThreshold?: 'none' | 'human' | 'dual_control' | 'board' | 'government_buyer';
  replayWindowSeconds?: number;
  rollbackPlanId?: string;
}

export interface TrustTransactionEvidence {
  evidenceId?: string;
  evidenceHash?: string;
  graphId?: string;
  graphObjectHash?: string;
  controlIds?: string[];
  frameworkCodes?: string[];
  freshnessDays?: number;
}

export interface TrustTransactionVerifier {
  verifierId?: string;
  roomId?: string;
  scope?: 'auditor' | 'customer' | 'prime_contractor' | 'insurer' | 'board' | 'regulator' | 'acquirer';
  accepted?: boolean;
  receiptHash?: string;
}

export interface TrustTransactionEconomics {
  riskScore?: number;
  estimatedDealImpactUsd?: number;
  estimatedDelayDays?: number;
  controlReuseCount?: number;
}

export interface TrustTransactionEnvelope {
  version: 'v1';
  transactionId: string;
  kind: TrustTransactionKind;
  status: TrustTransactionStatus;
  createdAt: string;
  tenantId?: number;
  orgSlug?: string;
  actor: TrustTransactionActor;
  action: {
    name: string;
    tool?: string;
    model?: string;
    idempotencyKey?: string;
    correlationId?: string;
  };
  policy?: TrustTransactionPolicy;
  dataBoundary: TrustDataBoundary;
  evidence?: TrustTransactionEvidence;
  verifier?: TrustTransactionVerifier;
  economics?: TrustTransactionEconomics;
  exportTargets?: Array<'evidence_graph' | 'copilot' | 'verifier_room' | 'procurement_packet' | 'benchmark_api' | 'diligence_api'>;
  previousHash?: string;
  transactionHash: string;
}

export type NewTrustTransaction = Omit<TrustTransactionEnvelope, 'version' | 'transactionId' | 'createdAt' | 'transactionHash'> & {
  transactionId?: string;
  createdAt?: string;
};

function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, nested]) => nested !== undefined)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([key, nested]) => [key, stable(nested)]),
    );
  }
  return value;
}

function stableStringify(value: unknown): string {
  return JSON.stringify(stable(value));
}

function sha256(value: unknown): string {
  return createHash('sha256').update(stableStringify(value)).digest('hex');
}

export function trustTransactionId(input: Pick<TrustTransactionEnvelope, 'kind' | 'actor' | 'action' | 'createdAt'>): string {
  return `trust_txn:${sha256(input).slice(0, 20)}`;
}

export function hashTrustTransaction(
  envelope: Omit<TrustTransactionEnvelope, 'transactionHash'> | TrustTransactionEnvelope,
): string {
  const { transactionHash: _transactionHash, ...hashable } = envelope as TrustTransactionEnvelope;
  return sha256(hashable);
}

export function createTrustTransaction(input: NewTrustTransaction): TrustTransactionEnvelope {
  const createdAt = input.createdAt ?? new Date().toISOString();
  const base: Omit<TrustTransactionEnvelope, 'transactionHash'> = {
    ...input,
    version: 'v1',
    createdAt,
    transactionId:
      input.transactionId ??
      trustTransactionId({
        kind: input.kind,
        actor: input.actor,
        action: input.action,
        createdAt,
      }),
  };
  return { ...base, transactionHash: hashTrustTransaction(base) };
}

export function verifyTrustTransaction(envelope: TrustTransactionEnvelope): { ok: boolean; transactionId: string; errors: string[] } {
  const errors: string[] = [];

  if (envelope.version !== 'v1') errors.push('unsupported_version');
  if (!envelope.transactionId) errors.push('missing_transaction_id');
  if (!envelope.kind) errors.push('missing_kind');
  if (!envelope.status) errors.push('missing_status');
  if (!envelope.actor?.id) errors.push('missing_actor_id');
  if (!envelope.actor?.type) errors.push('missing_actor_type');
  if (!envelope.action?.name) errors.push('missing_action_name');
  if (!envelope.dataBoundary) errors.push('missing_data_boundary');
  if (!envelope.transactionHash) errors.push('missing_transaction_hash');
  if (envelope.transactionHash && hashTrustTransaction(envelope) !== envelope.transactionHash) {
    errors.push('transaction_hash_mismatch');
  }
  if (envelope.policy?.decision === 'allow' && !envelope.policy.sandboxPolicy) {
    errors.push('allowed_transaction_missing_sandbox_policy');
  }
  if (envelope.kind === 'copilot_answer' && !envelope.evidence?.graphId && !envelope.evidence?.evidenceHash) {
    errors.push('copilot_answer_missing_proof');
  }
  if (envelope.kind === 'verifier_receipt' && !envelope.verifier?.receiptHash) {
    errors.push('verifier_receipt_missing_hash');
  }

  return { ok: errors.length === 0, transactionId: envelope.transactionId, errors };
}

export function redactTrustTransactionForSharing(envelope: TrustTransactionEnvelope): TrustTransactionEnvelope {
  const redactedActor: TrustTransactionActor = {
    ...envelope.actor,
    id: `redacted:${sha256(envelope.actor.id).slice(0, 12)}`,
    did: envelope.actor.did ? `redacted:${sha256(envelope.actor.did).slice(0, 12)}` : undefined,
  };

  return {
    ...envelope,
    tenantId: undefined,
    actor: redactedActor,
    action: {
      ...envelope.action,
      idempotencyKey: envelope.action.idempotencyKey
        ? `redacted:${sha256(envelope.action.idempotencyKey).slice(0, 12)}`
        : undefined,
    },
  };
}
