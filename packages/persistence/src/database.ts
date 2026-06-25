import postgres from 'postgres';
import type { Sql, TransactionSql } from 'postgres';

export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl?: boolean;
  maxConnections?: number;
}

export interface TenantContext {
  tenantId: string;
  userId: string;
  role: string;
}

export interface QueryResult<T = Record<string, unknown>> {
  rows: T[];
  rowCount: number;
}

export class Database {
  private config: DatabaseConfig;
  private sql: Sql;
  private closed = false;

  constructor(config: DatabaseConfig) {
    this.config = config;
    this.sql = postgres({
      host: config.host,
      port: config.port,
      database: config.database,
      username: config.username,
      password: config.password,
      ssl: config.ssl ? { rejectUnauthorized: false } : false,
      max: config.maxConnections ?? 10,
      idle_timeout: 20,
      connect_timeout: 10,
    });
  }

  get connectionConfig() { return this.config; }

  async query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<QueryResult<T>> {
    this.ensureOpen();
    const result = params && params.length > 0
      ? await this.sql.unsafe(sql, params as any[])
      : await this.sql.unsafe(sql);
    return {
      rows: result as unknown as T[],
      rowCount: (result as unknown as { count: number }).count ?? result.length,
    };
  }

  async execute(sql: string, params?: unknown[]): Promise<void> {
    this.ensureOpen();
    if (params && params.length > 0) {
      await this.sql.unsafe(sql, params as any[]);
    } else {
      await this.sql.unsafe(sql);
    }
  }

  async begin<T>(fn: (sql: TransactionSql) => T | Promise<T>): Promise<T> {
    this.ensureOpen();
    return this.sql.begin(fn) as Promise<T>;
  }

  async healthCheck(): Promise<boolean> {
    try {
      await this.sql`SELECT 1`;
      return true;
    } catch {
      return false;
    }
  }

  async close(): Promise<void> {
    if (!this.closed) {
      this.closed = true;
      await this.sql.end();
    }
  }

  private ensureOpen(): void {
    if (this.closed) {
      throw new Error('Database connection is closed');
    }
  }
}
