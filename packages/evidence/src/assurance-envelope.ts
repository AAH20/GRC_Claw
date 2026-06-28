import { createHash } from 'node:crypto';
import type { ActionLedgerEvent } from './action-ledger.js';

export interface AssuranceEnvelope {
  version: 'v1';
  actionId: string;
  tenantId: number;
  sessionId: string;
  tool: string;
  idempotencyKey?: string;
  createdAt: string;
  updatedAt: string;
  intent: { argsHash?: string; argKeys?: string[]; ledgerHash: string };
  policy?: { executionState: string; allowed: boolean; reason?: string; requiresApproval?: boolean; ledgerHash: string };
  result?: {
    executionState: string;
    outputHash?: string;
    evidenceId?: string;
    targetReceipt?: string;
    ledgerHash: string;
  };
  identity?: { agentDid?: string; status?: 'provisional' | 'verified' };
  assurance?: { riskScore?: number; blastRadiusImpact?: number; controlId?: string };
}

export interface AssuranceEnvelopeVerification {
  ok: boolean;
  actionId: string;
  envelopeHash: string;
  checkedAt: string;
  errors: string[];
}

function stableSerialize(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableSerialize(item)).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    return `{${Object.entries(value as Record<string, unknown>)
      .filter(([, item]) => item !== undefined)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, item]) => `${JSON.stringify(key)}:${stableSerialize(item)}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

export function hashAssuranceEnvelope(envelope: AssuranceEnvelope): string {
  return createHash('sha256').update(stableSerialize(envelope)).digest('hex');
}

/** Build a redacted, portable action receipt from hash-chained ledger events. */
export function createAssuranceEnvelope(input: {
  intent: ActionLedgerEvent;
  decision?: ActionLedgerEvent;
  result?: ActionLedgerEvent;
  identity?: AssuranceEnvelope['identity'];
  assurance?: AssuranceEnvelope['assurance'];
}): AssuranceEnvelope {
  const { intent, decision, result } = input;
  return {
    version: 'v1',
    actionId: intent.actionId,
    tenantId: intent.tenantId,
    sessionId: intent.sessionId,
    tool: intent.tool,
    idempotencyKey: intent.idempotencyKey,
    createdAt: intent.at,
    updatedAt: result?.at ?? decision?.at ?? intent.at,
    intent: { argsHash: intent.argsHash, argKeys: intent.argKeys, ledgerHash: intent.hash },
    policy: decision
      ? {
          executionState: decision.executionState,
          allowed: decision.executionState === 'executing',
          reason: decision.decisionReason,
          requiresApproval: decision.requiresApproval,
          ledgerHash: decision.hash,
        }
      : undefined,
    result: result
      ? {
          executionState: result.executionState,
          outputHash: result.outputHash,
          evidenceId: result.evidenceId,
          targetReceipt: result.targetReceipt,
          ledgerHash: result.hash,
        }
      : undefined,
    identity: input.identity,
    assurance: input.assurance,
  };
}

/** Verify an assurance receipt is complete enough for auditors and contains no raw payloads. */
export function verifyAssuranceEnvelope(envelope: AssuranceEnvelope): AssuranceEnvelopeVerification {
  const errors: string[] = [];

  if (envelope.version !== 'v1') errors.push('unsupported_version');
  if (!envelope.actionId) errors.push('missing_action_id');
  if (!Number.isFinite(envelope.tenantId)) errors.push('missing_tenant_id');
  if (!envelope.sessionId) errors.push('missing_session_id');
  if (!envelope.tool) errors.push('missing_tool');
  if (!envelope.createdAt) errors.push('missing_created_at');
  if (!envelope.updatedAt) errors.push('missing_updated_at');
  if (!envelope.intent?.ledgerHash) errors.push('missing_intent_ledger_hash');
  if (envelope.policy && !envelope.policy.ledgerHash) errors.push('missing_policy_ledger_hash');
  if (envelope.result && !envelope.result.ledgerHash) errors.push('missing_result_ledger_hash');

  const serialized = JSON.stringify({
    idempotencyKey: envelope.idempotencyKey,
    identity: envelope.identity,
    assurance: envelope.assurance,
  });
  const rawPayloadMarkers = ['password', 'secret', 'token', 'apiKey', 'privateKey'];
  for (const marker of rawPayloadMarkers) {
    if (serialized.includes(`"${marker}":`)) {
      errors.push(`raw_payload_marker_${marker}`);
    }
  }

  return {
    ok: errors.length === 0,
    actionId: envelope.actionId,
    envelopeHash: hashAssuranceEnvelope(envelope),
    checkedAt: new Date().toISOString(),
    errors,
  };
}

/** Return an auditor-safe receipt with only hashes, identity, policy, and assurance metadata. */
export function redactAssuranceEnvelopeForSharing(envelope: AssuranceEnvelope): AssuranceEnvelope {
  return {
    ...envelope,
    idempotencyKey: envelope.idempotencyKey ? `redacted:${hashAssuranceEnvelope(envelope).slice(0, 12)}` : undefined,
    intent: {
      argsHash: envelope.intent.argsHash,
      argKeys: envelope.intent.argKeys,
      ledgerHash: envelope.intent.ledgerHash,
    },
    policy: envelope.policy,
    result: envelope.result,
  };
}
