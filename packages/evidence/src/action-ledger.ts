import { createHash, randomUUID } from 'node:crypto';
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname } from 'node:path';

export type ActionExecutionState =
  | 'intent_recorded'
  | 'approval_required'
  | 'denied'
  | 'executing'
  | 'simulated'
  | 'recorded'
  | 'executed'
  | 'verified'
  | 'not_configured'
  | 'failed';

export interface ActionLedgerEvent {
  sequence: number;
  actionId: string;
  at: string;
  kind: 'intent' | 'decision' | 'result';
  tenantId: number;
  sessionId: string;
  tool: string;
  idempotencyKey?: string;
  executionState: ActionExecutionState;
  decisionReason?: string;
  requiresApproval?: boolean;
  argsHash?: string;
  argKeys?: string[];
  outputHash?: string;
  evidenceId?: string;
  targetReceipt?: string;
  previousHash: string;
  hash: string;
}

type ActionEventInput = Omit<ActionLedgerEvent, 'sequence' | 'at' | 'previousHash' | 'hash'> & {
  at?: string;
};

const GENESIS_HASH = '0'.repeat(64);

function sha256(value: string): string {
  return createHash('sha256').update(value).digest('hex');
}

function hashable(event: Omit<ActionLedgerEvent, 'hash'>): string {
  return JSON.stringify({
    sequence: event.sequence,
    actionId: event.actionId,
    at: event.at,
    kind: event.kind,
    tenantId: event.tenantId,
    sessionId: event.sessionId,
    tool: event.tool,
    idempotencyKey: event.idempotencyKey,
    executionState: event.executionState,
    decisionReason: event.decisionReason,
    requiresApproval: event.requiresApproval,
    argsHash: event.argsHash,
    argKeys: event.argKeys,
    outputHash: event.outputHash,
    evidenceId: event.evidenceId,
    targetReceipt: event.targetReceipt,
    previousHash: event.previousHash,
  });
}

/**
 * Append-only local proof of an agent action. Payloads are represented by hashes and key names,
 * keeping sensitive request and response content out of the operational ledger.
 */
export class ActionLedger {
  private readonly events: ActionLedgerEvent[] = [];

  constructor(private readonly filePath?: string) {
    if (filePath && existsSync(filePath)) {
      for (const line of readFileSync(filePath, 'utf8').split('\n').filter(Boolean)) {
        this.events.push(JSON.parse(line) as ActionLedgerEvent);
      }
    }
  }

  recordIntent(input: {
    tenantId: number;
    sessionId: string;
    tool: string;
    args: Record<string, unknown>;
    idempotencyKey?: string;
  }): ActionLedgerEvent {
    return this.append({
      actionId: randomUUID(),
      kind: 'intent',
      tenantId: input.tenantId,
      sessionId: input.sessionId,
      tool: input.tool,
      idempotencyKey: input.idempotencyKey,
      executionState: 'intent_recorded',
      argsHash: sha256(JSON.stringify(input.args)),
      argKeys: Object.keys(input.args).sort(),
    });
  }

  recordDecision(
    intent: ActionLedgerEvent,
    input: { allowed: boolean; reason: string; requiresApproval: boolean }
  ): ActionLedgerEvent {
    return this.append({
      actionId: intent.actionId,
      kind: 'decision',
      tenantId: intent.tenantId,
      sessionId: intent.sessionId,
      tool: intent.tool,
      idempotencyKey: intent.idempotencyKey,
      executionState: input.allowed
        ? 'executing'
        : input.requiresApproval
          ? 'approval_required'
          : 'denied',
      decisionReason: input.reason,
      requiresApproval: input.requiresApproval,
    });
  }

  recordResult(
    intent: ActionLedgerEvent,
    input: {
      executionState: Exclude<ActionExecutionState, 'intent_recorded' | 'approval_required' | 'denied' | 'executing'>;
      output?: Record<string, unknown>;
      evidenceId?: string;
      targetReceipt?: string;
    }
  ): ActionLedgerEvent {
    return this.append({
      actionId: intent.actionId,
      kind: 'result',
      tenantId: intent.tenantId,
      sessionId: intent.sessionId,
      tool: intent.tool,
      idempotencyKey: intent.idempotencyKey,
      executionState: input.executionState,
      outputHash: input.output ? sha256(JSON.stringify(input.output)) : undefined,
      evidenceId: input.evidenceId,
      targetReceipt: input.targetReceipt,
    });
  }

  list(limit = 100): ActionLedgerEvent[] {
    return this.events.slice(-Math.max(1, Math.min(limit, 500))).reverse();
  }

  verify(): { ok: boolean; checked: number; error?: string } {
    let previousHash = GENESIS_HASH;
    for (const event of this.events) {
      if (event.previousHash !== previousHash) {
        return { ok: false, checked: event.sequence - 1, error: `chain_break_at_${event.sequence}` };
      }
      const { hash, ...body } = event;
      if (sha256(hashable(body)) !== hash) {
        return { ok: false, checked: event.sequence - 1, error: `hash_mismatch_at_${event.sequence}` };
      }
      previousHash = event.hash;
    }
    return { ok: true, checked: this.events.length };
  }

  private append(input: ActionEventInput): ActionLedgerEvent {
    const previousHash = this.events.at(-1)?.hash ?? GENESIS_HASH;
    const withoutHash: Omit<ActionLedgerEvent, 'hash'> = {
      ...input,
      sequence: this.events.length + 1,
      at: input.at ?? new Date().toISOString(),
      previousHash,
    };
    const event: ActionLedgerEvent = { ...withoutHash, hash: sha256(hashable(withoutHash)) };
    this.events.push(event);
    if (this.filePath) {
      mkdirSync(dirname(this.filePath), { recursive: true });
      appendFileSync(this.filePath, `${JSON.stringify(event)}\n`, { mode: 0o600 });
    }
    return event;
  }
}
