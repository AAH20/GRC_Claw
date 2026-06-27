import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { RBACEngine } from "./RBACEngine.js";

function createEngine(): RBACEngine {
  return new RBACEngine({ jwtSecret: "test-secret-key-12345" });
}

describe("RBACEngine", () => {
  describe("Tenant Management", () => {
    it("creates a tenant", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      assert.ok(tenant.id.startsWith("tenant-"));
      assert.equal(tenant.name, "Acme Corp");
      assert.ok(tenant.createdAt);
    });

    it("retrieves a tenant", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      const retrieved = engine.getTenant(tenant.id);
      assert.deepStrictEqual(retrieved, tenant);
    });

    it("returns undefined for unknown tenant", () => {
      const engine = createEngine();
      assert.equal(engine.getTenant("unknown"), undefined);
    });
  });

  describe("Role Assignment", () => {
    it("assigns a role to a user", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      const assignment = engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      assert.equal(assignment.userId, "user-1");
      assert.equal(assignment.role, "admin");
      assert.equal(assignment.scope, "global");
      assert.equal(assignment.tenantId, tenant.id);
    });

    it("retrieves user roles", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      engine.assignRole("user-1", "auditor", "entity", tenant.id, "system", "entity-1");
      const roles = engine.getUserRoles("user-1", tenant.id);
      assert.equal(roles.length, 2);
    });

    it("removes a specific role", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      engine.assignRole("user-1", "auditor", "global", tenant.id, "system");
      const removed = engine.removeRole("user-1", tenant.id, "admin");
      assert.equal(removed, true);
      const roles = engine.getUserRoles("user-1", tenant.id);
      assert.equal(roles.length, 1);
      assert.equal(roles[0].role, "auditor");
    });

    it("removes all roles for a user", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      engine.assignRole("user-1", "auditor", "global", tenant.id, "system");
      const removed = engine.removeRole("user-1", tenant.id);
      assert.equal(removed, true);
      assert.equal(engine.getUserRoles("user-1", tenant.id).length, 0);
    });

    it("throws for unknown role", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      assert.throws(
        () => engine.assignRole("user-1", "nonexistent" as any, "global", tenant.id, "system"),
        /Role not found/
      );
    });
  });

  describe("Permission Checking", () => {
    it("allows admin to write frameworks", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      const result = engine.checkPermission({
        userId: "user-1",
        tenantId: tenant.id,
        resource: "frameworks",
        action: "write",
      });
      assert.equal(result.allowed, true);
      assert.equal(result.role, "admin");
    });

    it("denies viewer from writing frameworks", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "viewer", "global", tenant.id, "system");
      const result = engine.checkPermission({
        userId: "user-1",
        tenantId: tenant.id,
        resource: "frameworks",
        action: "write",
      });
      assert.equal(result.allowed, false);
    });

    it("allows auditor to export evidence", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "auditor", "global", tenant.id, "system");
      const result = engine.checkPermission({
        userId: "user-1",
        tenantId: tenant.id,
        resource: "evidence",
        action: "export",
      });
      assert.equal(result.allowed, true);
    });

    it("allows compliance_officer to approve policies", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "compliance_officer", "global", tenant.id, "system");
      const result = engine.checkPermission({
        userId: "user-1",
        tenantId: tenant.id,
        resource: "policies",
        action: "approve",
      });
      assert.equal(result.allowed, true);
    });

    it("denies user with no assignments", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      const result = engine.checkPermission({
        userId: "unknown-user",
        tenantId: tenant.id,
        resource: "frameworks",
        action: "read",
      });
      assert.equal(result.allowed, false);
      assert.equal(result.reason, "No role assignments found");
    });

    it("hasPermission returns boolean", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      assert.equal(engine.hasPermission("user-1", tenant.id, "frameworks", "read"), true);
      assert.equal(engine.hasPermission("user-1", tenant.id, "tenants", "delete"), true);
      assert.equal(engine.hasPermission("user-2", tenant.id, "frameworks", "read"), false);
    });
  });

  describe("Scope Validation", () => {
    it("global scope allows access to all resources", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      const result = engine.checkPermission({
        userId: "user-1",
        tenantId: tenant.id,
        resource: "frameworks",
        action: "write",
      });
      assert.equal(result.allowed, true);
    });

    it("entity scope restricts to specific entity", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "compliance_officer", "entity", tenant.id, "system", "entity-1");
      const result = engine.checkPermission({
        userId: "user-1",
        tenantId: tenant.id,
        resource: "evidence",
        action: "write",
        scopeId: "entity-1",
      });
      assert.equal(result.allowed, true);
    });

    it("entity scope denies access to different entity", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "compliance_officer", "entity", tenant.id, "system", "entity-1");
      const result = engine.checkPermission({
        userId: "user-1",
        tenantId: tenant.id,
        resource: "evidence",
        action: "write",
        scopeId: "entity-2",
      });
      assert.equal(result.allowed, false);
    });
  });

  describe("JWT Token", () => {
    it("generates and verifies a valid JWT", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      const token = engine.generateJWT("user-1", tenant.id);
      assert.ok(token);
      assert.equal(token.split(".").length, 3);

      const payload = engine.verifyJWT(token);
      assert.ok(payload);
      assert.equal(payload.sub, "user-1");
      assert.equal(payload.tenant_id, tenant.id);
      assert.equal(payload.role, "admin");
      assert.ok(payload.permissions.length > 0);
    });

    it("rejects invalid token", () => {
      const engine = createEngine();
      assert.equal(engine.verifyJWT("invalid.token.here"), null);
    });

    it("rejects token with wrong secret", () => {
      const engine1 = new RBACEngine({ jwtSecret: "secret-1" });
      const engine2 = new RBACEngine({ jwtSecret: "secret-2" });
      const tenant = engine1.createTenant("Acme Corp");
      engine1.assignRole("user-1", "admin", "global", tenant.id, "system");
      const token = engine1.generateJWT("user-1", tenant.id);
      assert.equal(engine2.verifyJWT(token), null);
    });

    it("rejects expired token", () => {
      const engine = new RBACEngine({ jwtSecret: "test", jwtExpiresIn: -1 });
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      const token = engine.generateJWT("user-1", tenant.id);
      assert.equal(engine.verifyJWT(token), null);
    });
  });

  describe("Audit Logging", () => {
    it("logs permission checks", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      engine.checkPermission({
        userId: "user-1",
        tenantId: tenant.id,
        resource: "frameworks",
        action: "read",
      });
      const logs = engine.getAuditLog(tenant.id);
      const permLog = logs.find((l) => l.resource === "frameworks");
      assert.ok(permLog);
      assert.equal(permLog.action, "read");
      assert.equal(permLog.allowed, true);
    });

    it("logs role assignments", () => {
      const engine = createEngine();
      const tenant = engine.createTenant("Acme Corp");
      engine.assignRole("user-1", "admin", "global", tenant.id, "system");
      const logs = engine.getAuditLog(tenant.id);
      assert.ok(logs.length > 0);
      assert.equal(logs[0].resource, "roles");
      assert.equal(logs[0].action, "write");
    });

    it("filters audit log by tenant", () => {
      const engine = createEngine();
      const tenant1 = engine.createTenant("Tenant 1");
      const tenant2 = engine.createTenant("Tenant 2");
      engine.assignRole("user-1", "admin", "global", tenant1.id, "system");
      engine.assignRole("user-2", "admin", "global", tenant2.id, "system");
      const logs1 = engine.getAuditLog(tenant1.id);
      assert.ok(logs1.every((l) => l.tenantId === tenant1.id));
    });
  });

  describe("Role Permissions", () => {
    it("returns permissions for a role", () => {
      const engine = createEngine();
      const perms = engine.getRolePermissions("admin");
      assert.ok(perms.length > 0);
      assert.ok(perms.some((p) => p.resource === "frameworks"));
    });

    it("returns all built-in roles", () => {
      const engine = createEngine();
      const roles = engine.getAllRoles();
      assert.ok(roles.length >= 5);
      assert.ok(roles.some((r) => r.name === "admin"));
      assert.ok(roles.some((r) => r.name === "viewer"));
    });
  });

  describe("Multi-Tenant Isolation", () => {
    it("isolates users across tenants", () => {
      const engine = createEngine();
      const tenant1 = engine.createTenant("Tenant 1");
      const tenant2 = engine.createTenant("Tenant 2");
      engine.assignRole("user-1", "admin", "global", tenant1.id, "system");
      engine.assignRole("user-1", "viewer", "global", tenant2.id, "system");

      const roles1 = engine.getUserRoles("user-1", tenant1.id);
      const roles2 = engine.getUserRoles("user-1", tenant2.id);
      assert.equal(roles1[0].role, "admin");
      assert.equal(roles2[0].role, "viewer");
    });

    it("prevents cross-tenant permission leakage", () => {
      const engine = createEngine();
      const tenant1 = engine.createTenant("Tenant 1");
      const tenant2 = engine.createTenant("Tenant 2");
      engine.assignRole("user-1", "admin", "global", tenant1.id, "system");

      assert.equal(engine.hasPermission("user-1", tenant1.id, "frameworks", "write"), true);
      assert.equal(engine.hasPermission("user-1", tenant2.id, "frameworks", "write"), false);
    });
  });
});
