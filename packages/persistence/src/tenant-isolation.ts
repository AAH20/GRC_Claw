import type { Database, TenantContext } from './database.js';

export interface TenantIsolationConfig {
  enableRLS: boolean;
  auditAccess: boolean;
  crossTenantLookup: boolean;
}

const DEFAULT_CONFIG: TenantIsolationConfig = {
  enableRLS: true,
  auditAccess: true,
  crossTenantLookup: false,
};

const RLS_TABLES = [
  'users',
  'compliance_state',
  'evidence',
  'drift_events',
  'security_events',
  'agents',
  'playbook_executions',
  'action_ledger',
  'remediation_plans',
  'compliance_snapshots',
];

export class TenantIsolation {
  private config: TenantIsolationConfig;
  private db?: Database;

  constructor(config: Partial<TenantIsolationConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  setDatabase(db: Database): void {
    this.db = db;
  }

  generateRLSPolicies(): string[] {
    return RLS_TABLES.map((table) => `
ALTER TABLE ${table} ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_${table} ON ${table}
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
`);
  }

  async setTenantContext(ctx: TenantContext): Promise<void> {
    if (!this.db) {
      throw new Error('Database not configured. Call setDatabase() before setTenantContext().');
    }
    await this.db.execute(
      "SELECT set_config('app.current_tenant_id', $1, true)",
      [ctx.tenantId],
    );
  }

  validateTenantAccess(ctx: TenantContext, resourceTenantId: string): boolean {
    if (ctx.tenantId === resourceTenantId) return true;
    if (this.config.crossTenantLookup && ctx.role === 'admin') return true;
    return false;
  }

  generateMigration(): string {
    const policies = this.generateRLSPolicies();
    return `
-- GRC_Claw Multi-Tenant Row-Level Security Migration
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE OR REPLACE FUNCTION set_current_tenant(tenant_uuid UUID)
RETURNS VOID AS $$
BEGIN
  PERFORM set_config('app.current_tenant_id', tenant_uuid::text, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TABLE IF NOT EXISTS tenant_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID,
  action VARCHAR(10) NOT NULL,
  table_name VARCHAR(100) NOT NULL,
  record_id UUID,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant_timestamp ON tenant_audit_log(tenant_id, timestamp DESC);

${policies.join('\n')}
`;
  }
}
