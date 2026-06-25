import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { TenantIsolation } from "./tenant-isolation.js";

describe("TenantIsolation", () => {
  it("should generate RLS policies for all tables", () => {
    const isolation = new TenantIsolation();
    const policies = isolation.generateRLSPolicies();
    assert.ok(policies.length > 0);
    assert.ok(policies.some((p) => p.includes("users")));
    assert.ok(policies.some((p) => p.includes("compliance_state")));
    assert.ok(policies.some((p) => p.includes("evidence")));
  });

  it("should validate tenant access correctly", () => {
    const isolation = new TenantIsolation();
    const ctx = { tenantId: "tenant-1", userId: "user-1", role: "admin" };

    assert.ok(isolation.validateTenantAccess(ctx, "tenant-1"));
    assert.ok(!isolation.validateTenantAccess(ctx, "tenant-2"));
  });

  it("should allow cross-tenant admin lookup when enabled", () => {
    const isolation = new TenantIsolation({ crossTenantLookup: true });
    const ctx = { tenantId: "tenant-1", userId: "user-1", role: "admin" };

    assert.ok(isolation.validateTenantAccess(ctx, "tenant-2"));
  });

  it("should deny cross-tenant non-admin lookup", () => {
    const isolation = new TenantIsolation({ crossTenantLookup: true });
    const ctx = { tenantId: "tenant-1", userId: "user-1", role: "viewer" };

    assert.ok(!isolation.validateTenantAccess(ctx, "tenant-2"));
  });

  it("should generate valid migration SQL", () => {
    const isolation = new TenantIsolation();
    const migration = isolation.generateMigration();
    assert.ok(migration.includes("ENABLE ROW LEVEL SECURITY"));
    assert.ok(migration.includes("set_current_tenant"));
    assert.ok(migration.includes("tenant_audit_log"));
  });
});

describe("PersistenceLayer", () => {
  it("should create persistence layer without database connection", async () => {
    const { PersistenceLayer } = await import("./index.js");
    const layer = new PersistenceLayer({
      host: "localhost",
      port: 5432,
      database: "test",
      username: "test",
      password: "test",
    });
    assert.ok(layer.database);
    assert.ok(layer.tenantIsolation);
  });
});
