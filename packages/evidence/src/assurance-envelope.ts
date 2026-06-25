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
