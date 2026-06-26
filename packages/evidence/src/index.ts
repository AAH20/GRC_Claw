import { createHash } from 'node:crypto';

export * from './action-ledger.js';
export * from './assurance-envelope.js';

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

export class EvidenceStore {
  private readonly records = new Map<string, EvidenceRecord>();
  private readonly db?: EvidenceDatabase;

  constructor(database?: EvidenceDatabase) {
    this.db = database;
  }

  static hashContent(buffer: Buffer | string): string {
    return createHash('sha256').update(buffer).digest('hex');
  }

  attach(input: Omit<EvidenceRecord, 'id' | 'sha256'> & { content?: Buffer | string }): EvidenceRecord {
    const sha256 =
      input.content !== undefined
        ? EvidenceStore.hashContent(input.content)
        : EvidenceStore.hashContent(`${input.uri}|${input.collectedAt}`);
    const id = `ev-${sha256.slice(0, 16)}`;
    const record: EvidenceRecord = { ...input, id, sha256 };
    this.records.set(id, record);

    if (this.db) {
      const db = this.db;
      void db.execute(
        `INSERT INTO evidence (id, tenant_id, control_id, sha256, uri, metadata, lineage, collected_at, created_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
         ON CONFLICT (id) DO NOTHING`,
        [
          id,
          String(input.tenantId),
          input.controlId,
          sha256,
          input.uri,
          JSON.stringify({}),
          JSON.stringify(input.lineage),
          input.collectedAt,
        ],
      ).catch(() => {
        // fall back to in-memory only
      });
    }

    return record;
  }

  get(id: string): EvidenceRecord | undefined {
    return this.records.get(id);
  }

  listByControl(controlId: string): EvidenceRecord[] {
    return [...this.records.values()].filter((r) => r.controlId === controlId);
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
