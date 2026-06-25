import { Database, type DatabaseConfig, type TenantContext } from "./database.js";
import { TenantIsolation } from "./tenant-isolation.js";

export interface PersistenceConfig extends DatabaseConfig {
  tenantIsolation?: {
    enableRLS?: boolean;
    auditAccess?: boolean;
    crossTenantLookup?: boolean;
  };
}

export class PersistenceLayer {
  private db: Database;
  private isolation: TenantIsolation;

  constructor(config: PersistenceConfig) {
    this.db = new Database(config);
    this.isolation = new TenantIsolation(config.tenantIsolation);
  }

  get database() { return this.db; }
  get tenantIsolation() { return this.isolation; }

  async initialize(): Promise<void> {
    const migration = this.isolation.generateMigration();
    await this.db.execute(migration);
  }

  async withTenant<T>(ctx: TenantContext, fn: (db: Database) => Promise<T>): Promise<T> {
    await this.isolation.setTenantContext(ctx);
    return fn(this.db);
  }

  async close() {
    await this.db.close();
  }
}

export { Database } from "./database.js";
export { TenantIsolation } from "./tenant-isolation.js";
export type { DatabaseConfig, TenantContext } from "./database.js";
export * from "./schema/index.js";
