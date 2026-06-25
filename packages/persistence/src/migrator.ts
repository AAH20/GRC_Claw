import { createHash } from 'node:crypto';
import type { Database } from './database.js';

export interface Migration {
  name: string;
  up: string;
  down: string;
}

export interface MigrationStatus {
  name: string;
  applied: boolean;
}

export class Migrator {
  private db: Database;
  private migrations: Migration[];

  constructor(db: Database, migrations: Migration[] = []) {
    this.db = db;
    this.migrations = migrations;
  }

  async ensureMigrationsTable(): Promise<void> {
    await this.db.execute(`
      CREATE TABLE IF NOT EXISTS _migrations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        checksum VARCHAR(64) NOT NULL
      )
    `);
  }

  async getAppliedMigrations(): Promise<string[]> {
    const result = await this.db.query<{ name: string }>(
      'SELECT name FROM _migrations ORDER BY id',
    );
    return result.rows.map((r) => r.name);
  }

  async up(): Promise<string[]> {
    await this.ensureMigrationsTable();
    const applied = await this.getAppliedMigrations();
    const pending = this.migrations.filter((m) => !applied.includes(m.name));
    const appliedNames: string[] = [];

    for (const migration of pending) {
      await this.db.execute(migration.up);
      const checksum = this.computeChecksum(migration.up);
      await this.db.execute(
        'INSERT INTO _migrations (name, checksum) VALUES ($1, $2)',
        [migration.name, checksum],
      );
      appliedNames.push(migration.name);
    }

    return appliedNames;
  }

  async down(steps: number = 1): Promise<string[]> {
    await this.ensureMigrationsTable();
    const applied = await this.getAppliedMigrations();
    const toRevert = applied.slice(-steps).reverse();
    const revertedNames: string[] = [];

    for (const name of toRevert) {
      const migration = this.migrations.find((m) => m.name === name);
      if (!migration) {
        throw new Error(`Migration "${name}" not found in registered migrations`);
      }
      await this.db.execute(migration.down);
      await this.db.execute('DELETE FROM _migrations WHERE name = $1', [name]);
      revertedNames.push(name);
    }

    return revertedNames;
  }

  async status(): Promise<MigrationStatus[]> {
    await this.ensureMigrationsTable();
    const applied = await this.getAppliedMigrations();
    return this.migrations.map((m) => ({
      name: m.name,
      applied: applied.includes(m.name),
    }));
  }

  private computeChecksum(sql: string): string {
    return createHash('sha256').update(sql).digest('hex');
  }
}
