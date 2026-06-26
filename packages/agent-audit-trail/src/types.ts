export interface AuditRecord {
  id: string;
  timestamp: string;
  agentDid: string;
  tool: string;
  args: Record<string, unknown>;
  result: Record<string, unknown>;
  previousHash: string;
  hash: string;
}

export interface AuditQuery {
  agentDid?: string;
  tool?: string;
  from?: string;
  to?: string;
  limit?: number;
  offset?: number;
}

export interface AuditExportOptions {
  format: 'json' | 'csv';
  agentDid?: string;
  tool?: string;
  from?: string;
  to?: string;
}

export interface IntegrityResult {
  valid: boolean;
  totalRecords: number;
  brokenAt: number | null;
  error?: string;
}
