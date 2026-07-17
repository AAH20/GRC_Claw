import { createHash } from 'node:crypto';

export * from './action-ledger.js';
export * from './assurance-envelope.js';
export * from './agent-trust-passport.js';

export interface EvidenceRecord {
  id: string;
  controlId: string;
  tenantId: number;
  sha256: string;
  uri: string;
  collectedAt: string;
  lineage: { parentHash?: string; source: string };
}

export interface EvidenceDatabase {
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount: number }>;
  execute(sql: string, params?: unknown[]): Promise<void>;
}

const MAX_RETRIES = 3;
const BASE_BACKOFF_MS = 100;

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class EvidenceStore {
  private readonly records = new Map<string, EvidenceRecord>();
  private readonly db?: EvidenceDatabase;
  private pendingWrites: Promise<void>[] = [];

  constructor(database?: EvidenceDatabase) {
    this.db = database;
  }

  static hashContent(buffer: Buffer | string): string {
    return createHash('sha256').update(buffer).digest('hex');
  }

  private async writeToDbWithRetry(record: EvidenceRecord): Promise<void> {
    if (!this.db) return;
    let lastError: Error | undefined;
    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        await this.db.execute(
          `INSERT INTO evidence (id, tenant_id, control_id, sha256, uri, metadata, lineage, collected_at, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
           ON CONFLICT (id) DO NOTHING`,
          [
            record.id,
            String(record.tenantId),
            record.controlId,
            record.sha256,
            record.uri,
            JSON.stringify({}),
            JSON.stringify(record.lineage),
            record.collectedAt,
          ],
        );
        return;
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        if (attempt < MAX_RETRIES - 1) {
          await sleep(BASE_BACKOFF_MS * Math.pow(2, attempt));
        }
      }
    }
    console.warn(
      `[EVIDENCE] PostgreSQL write failed after ${MAX_RETRIES} retries for ${record.id}:`,
      lastError?.message,
    );
  }

  attach(input: Omit<EvidenceRecord, 'id' | 'sha256'> & { content?: Buffer | string }): EvidenceRecord {
    const sha256 =
      input.content !== undefined
        ? EvidenceStore.hashContent(input.content)
        : EvidenceStore.hashContent(`${input.uri}|${input.collectedAt}`);
    const id = `ev-${sha256.slice(0, 16)}`;
    const record: EvidenceRecord = { ...input, id, sha256 };

    // Write to PostgreSQL first, then update in-memory cache
    const writePromise = this.writeToDbWithRetry(record);
    this.pendingWrites.push(writePromise);

    // Update in-memory cache immediately for fast reads
    this.records.set(id, record);

    return record;
  }

  get(id: string): EvidenceRecord | undefined {
    return this.records.get(id);
  }

  /** Read a single evidence record from PostgreSQL (primary) with in-memory fallback */
  async getFromDb(id: string): Promise<EvidenceRecord | undefined> {
    if (this.db) {
      try {
        const { rows } = await this.db.query<{
          id: string;
          control_id: string;
          tenant_id: string;
          sha256: string;
          uri: string;
          collected_at: string;
          lineage: { parentHash?: string; source: string };
        }>(
          `SELECT id, control_id, tenant_id, sha256, uri, collected_at, lineage FROM evidence WHERE id = $1`,
          [id],
        );
        if (rows.length > 0) {
          const row = rows[0]!;
          const record: EvidenceRecord = {
            id: row.id,
            controlId: row.control_id,
            tenantId: Number(row.tenant_id),
            sha256: row.sha256,
            uri: row.uri,
            collectedAt: row.collected_at,
            lineage: row.lineage,
          };
          this.records.set(id, record);
          return record;
        }
      } catch {
        // fall back to in-memory
      }
    }
    return this.records.get(id);
  }

  /** Synchronous read from in-memory write-through cache */
  listByControl(controlId: string): EvidenceRecord[] {
    return [...this.records.values()].filter((r) => r.controlId === controlId);
  }

  /** Read evidence for a control from PostgreSQL (primary) with in-memory fallback */
  async listByControlFromDb(controlId: string): Promise<EvidenceRecord[]> {
    if (this.db) {
      try {
        const { rows } = await this.db.query<{
          id: string;
          control_id: string;
          tenant_id: string;
          sha256: string;
          uri: string;
          collected_at: string;
          lineage: { parentHash?: string; source: string };
        }>(
          `SELECT id, control_id, tenant_id, sha256, uri, collected_at, lineage FROM evidence WHERE control_id = $1`,
          [controlId],
        );
        if (rows.length > 0) {
          const results = rows.map((row) => ({
            id: row.id,
            controlId: row.control_id,
            tenantId: Number(row.tenant_id),
            sha256: row.sha256,
            uri: row.uri,
            collectedAt: row.collected_at,
            lineage: row.lineage,
          }));
          // Update cache with DB results
          for (const r of results) {
            this.records.set(r.id, r);
          }
          return results;
        }
      } catch {
        // fall back to in-memory
      }
    }
    return [...this.records.values()].filter((r) => r.controlId === controlId);
  }

  /** Flush all pending PostgreSQL writes */
  async flush(): Promise<void> {
    const pending = [...this.pendingWrites];
    this.pendingWrites = [];
    await Promise.allSettled(pending);
  }

  async loadFromDatabase(): Promise<void> {
    if (!this.db) return;
    try {
      const { rows } = await this.db.query<{
        id: string;
        control_id: string;
        tenant_id: string;
        sha256: string;
        uri: string;
        collected_at: string;
        lineage: { parentHash?: string; source: string };
      }>(
        `SELECT id, control_id, tenant_id, sha256, uri, collected_at, lineage FROM evidence`,
      );
      for (const row of rows) {
        const record: EvidenceRecord = {
          id: row.id,
          controlId: row.control_id,
          tenantId: Number(row.tenant_id),
          sha256: row.sha256,
          uri: row.uri,
          collectedAt: row.collected_at,
          lineage: row.lineage,
        };
        this.records.set(record.id, record);
      }
    } catch {
      // fall back to empty in-memory state
    }
  }
}
