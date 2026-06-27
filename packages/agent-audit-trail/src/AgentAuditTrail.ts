import { createHash } from 'node:crypto';
import { randomUUID } from 'node:crypto';
import type { AuditRecord, AuditQuery, AuditExportOptions, IntegrityResult } from './types.js';

const GENESIS_HASH = '0000000000000000000000000000000000000000000000000000000000000000';

export interface AuditDatabase {
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount: number }>;
  execute(sql: string, params?: unknown[]): Promise<void>;
}

export class AgentAuditTrail {
  private records: AuditRecord[] = [];
  private readonly db?: AuditDatabase;
  private pendingWrites: Promise<void>[] = [];

  constructor(database?: AuditDatabase) {
    this.db = database;
  }

  async initializeDatabase(): Promise<void> {
    if (!this.db) return;
    await this.db.execute(`
      CREATE TABLE IF NOT EXISTS agent_audit_trail (
        id TEXT PRIMARY KEY,
        agent_did TEXT NOT NULL,
        tool TEXT NOT NULL,
        arguments_hash TEXT NOT NULL,
        result_hash TEXT NOT NULL,
        chain_hash TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
      )
    `);
  }

  private argsHash(args: Record<string, unknown>): string {
    return createHash('sha256').update(JSON.stringify(args)).digest('hex');
  }

  private resultHash(result: Record<string, unknown>): string {
    return createHash('sha256').update(JSON.stringify(result)).digest('hex');
  }

  private async writeToDb(record: AuditRecord): Promise<void> {
    if (!this.db) return;
    try {
      await this.db.execute(
        `INSERT INTO agent_audit_trail (id, agent_did, tool, arguments_hash, result_hash, chain_hash, previous_hash, created_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
         ON CONFLICT (id) DO NOTHING`,
        [
          record.id,
          record.agentDid,
          record.tool,
          this.argsHash(record.args),
          this.resultHash(record.result),
          record.hash,
          record.previousHash,
          record.timestamp,
        ],
      );
    } catch (err) {
      console.warn(
        `[AUDIT] PostgreSQL write failed for ${record.id}:`,
        err instanceof Error ? err.message : String(err),
      );
    }
  }

  async loadFromDatabase(): Promise<void> {
    if (!this.db) return;
    try {
      const { rows } = await this.db.query<{
        id: string;
        agent_did: string;
        tool: string;
        arguments_hash: string;
        result_hash: string;
        chain_hash: string;
        previous_hash: string;
        created_at: string;
      }>(
        `SELECT id, agent_did, tool, arguments_hash, result_hash, chain_hash, previous_hash, created_at
         FROM agent_audit_trail ORDER BY created_at ASC`,
      );
      for (const row of rows) {
        const record: AuditRecord = {
          id: row.id,
          timestamp: row.created_at,
          agentDid: row.agent_did,
          tool: row.tool,
          args: {},
          result: {},
          previousHash: row.previous_hash,
          hash: row.chain_hash,
        };
        this.records.push(record);
      }
    } catch {
      // fall back to empty in-memory state
    }
  }

  record(agentDid: string, tool: string, args: Record<string, unknown>, result: Record<string, unknown>): AuditRecord {
    const previousHash = this.records.length > 0
      ? this.records[this.records.length - 1].hash
      : GENESIS_HASH;

    const id = randomUUID();
    const timestamp = new Date().toISOString();

    const payload = JSON.stringify({ id, timestamp, agentDid, tool, args, result, previousHash });
    const hash = createHash('sha256').update(payload).digest('hex');

    const record: AuditRecord = {
      id,
      timestamp,
      agentDid,
      tool,
      args,
      result,
      previousHash,
      hash,
    };

    this.records.push(record);

    // Write-through to PostgreSQL
    const writePromise = this.writeToDb(record);
    this.pendingWrites.push(writePromise);

    return record;
  }

  async flush(): Promise<void> {
    const pending = [...this.pendingWrites];
    this.pendingWrites = [];
    await Promise.allSettled(pending);
  }

  verify(): IntegrityResult {
    for (let i = 0; i < this.records.length; i++) {
      const record = this.records[i];

      if (i === 0 && record.previousHash !== GENESIS_HASH) {
        return { valid: false, totalRecords: this.records.length, brokenAt: 0, error: 'Genesis hash mismatch' };
      }

      if (i > 0 && record.previousHash !== this.records[i - 1].hash) {
        return { valid: false, totalRecords: this.records.length, brokenAt: i, error: `Chain broken at index ${i}: previousHash does not match prior record hash` };
      }

      const { hash: _expectedHash, ...rest } = record;
      const recomputed = createHash('sha256').update(JSON.stringify(rest)).digest('hex');
      if (recomputed !== record.hash) {
        return { valid: false, totalRecords: this.records.length, brokenAt: i, error: `Record ${i} hash tampered: expected ${recomputed} got ${record.hash}` };
      }
    }

    return { valid: true, totalRecords: this.records.length, brokenAt: null };
  }

  query(q: AuditQuery): AuditRecord[] {
    let results = [...this.records];

    if (q.agentDid) {
      results = results.filter(r => r.agentDid === q.agentDid);
    }
    if (q.tool) {
      results = results.filter(r => r.tool === q.tool);
    }
    if (q.from) {
      results = results.filter(r => r.timestamp >= q.from!);
    }
    if (q.to) {
      results = results.filter(r => r.timestamp <= q.to!);
    }

    const offset = q.offset ?? 0;
    const limit = q.limit ?? results.length;
    return results.slice(offset, offset + limit);
  }

  export(options: AuditExportOptions): string {
    let records = [...this.records];

    if (options.agentDid) {
      records = records.filter(r => r.agentDid === options.agentDid);
    }
    if (options.tool) {
      records = records.filter(r => r.tool === options.tool);
    }
    if (options.from) {
      records = records.filter(r => r.timestamp >= options.from!);
    }
    if (options.to) {
      records = records.filter(r => r.timestamp <= options.to!);
    }

    if (options.format === 'csv') {
      const header = 'id,timestamp,agentDid,tool,previousHash,hash';
      const rows = records.map(r =>
        [r.id, r.timestamp, r.agentDid, r.tool, r.previousHash, r.hash].join(',')
      );
      return [header, ...rows].join('\n');
    }

    return JSON.stringify(records, null, 2);
  }

  list(limit?: number): AuditRecord[] {
    if (limit) return this.records.slice(-limit);
    return [...this.records];
  }

  count(): number {
    return this.records.length;
  }
}
