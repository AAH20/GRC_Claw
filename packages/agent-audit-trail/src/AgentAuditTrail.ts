import { createHash } from 'node:crypto';
import { randomUUID } from 'node:crypto';
import type { AuditRecord, AuditQuery, AuditExportOptions, IntegrityResult } from './types.js';

const GENESIS_HASH = '0000000000000000000000000000000000000000000000000000000000000000';

export class AgentAuditTrail {
  private records: AuditRecord[] = [];

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
    return record;
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
