import { createHash } from 'node:crypto';

/** Stable id for dedupe on retry (ingest-oss-siem-ids-logs) */
export function stableEventUuid(parts: (string | number | undefined)[]): string {
  const payload = parts.filter((p) => p !== undefined && p !== '').join('|');
  const hash = createHash('sha256').update(payload).digest('hex').slice(0, 32);
  return `${hash.slice(0, 8)}-${hash.slice(8, 12)}-${hash.slice(12, 16)}-${hash.slice(16, 20)}-${hash.slice(20, 32)}`;
}
