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

export class EvidenceStore {
  private readonly records = new Map<string, EvidenceRecord>();

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
    return record;
  }

  get(id: string): EvidenceRecord | undefined {
    return this.records.get(id);
  }

  listByControl(controlId: string): EvidenceRecord[] {
    return [...this.records.values()].filter((r) => r.controlId === controlId);
  }
}
