import { createHash, randomUUID, createHmac } from "node:crypto";
import type {
  Role,
  RoleName,
  ScopeLevel,
  Resource,
  Action,
  Permission,
  UserRoleAssignment,
  TenantConfig,
  PermissionCheck,
  PermissionResult,
  AuditLogEntry,
  JWTPayload,
  RBACConfig,
  PermissionString,
} from "./types.js";

const BUILTIN_ROLES: Record<RoleName, Role> = {
  admin: {
    name: "admin",
    description: "Full system administrator with unrestricted access",
    permissions: [
      { resource: "frameworks", actions: ["read", "write", "delete", "manage"] },
      { resource: "evidence", actions: ["read", "write", "delete", "export"] },
      { resource: "policies", actions: ["read", "write", "delete", "approve"] },
      { resource: "controls", actions: ["read", "write", "delete"] },
      { resource: "assessments", actions: ["read", "write", "delete", "approve"] },
      { resource: "vendors", actions: ["read", "write", "delete"] },
      { resource: "risks", actions: ["read", "write", "delete"] },
      { resource: "incidents", actions: ["read", "write", "delete"] },
      { resource: "connectors", actions: ["read", "write", "delete", "manage"] },
      { resource: "users", actions: ["read", "write", "delete", "manage"] },
      { resource: "roles", actions: ["read", "write", "delete", "manage"] },
      { resource: "tenants", actions: ["read", "write", "delete", "manage"] },
      { resource: "audit_logs", actions: ["read", "export"] },
      { resource: "reports", actions: ["read", "write", "export"] },
      { resource: "settings", actions: ["read", "write"] },
    ],
  },
  compliance_officer: {
    name: "compliance_officer",
    description: "Manages compliance frameworks, policies, and evidence",
    permissions: [
      { resource: "frameworks", actions: ["read", "write"] },
      { resource: "evidence", actions: ["read", "write", "export"] },
      { resource: "policies", actions: ["read", "write", "approve"] },
      { resource: "controls", actions: ["read", "write"] },
      { resource: "assessments", actions: ["read", "write", "approve"] },
      { resource: "vendors", actions: ["read", "write"] },
      { resource: "risks", actions: ["read", "write"] },
      { resource: "incidents", actions: ["read", "write"] },
      { resource: "audit_logs", actions: ["read"] },
      { resource: "reports", actions: ["read", "write", "export"] },
    ],
  },
  auditor: {
    name: "auditor",
    description: "Read-only access for audit and review purposes",
    permissions: [
      { resource: "frameworks", actions: ["read"] },
      { resource: "evidence", actions: ["read", "export"] },
      { resource: "policies", actions: ["read"] },
      { resource: "controls", actions: ["read"] },
      { resource: "assessments", actions: ["read"] },
      { resource: "vendors", actions: ["read"] },
      { resource: "risks", actions: ["read"] },
      { resource: "incidents", actions: ["read"] },
      { resource: "audit_logs", actions: ["read", "export"] },
      { resource: "reports", actions: ["read", "export"] },
    ],
  },
  viewer: {
    name: "viewer",
    description: "Basic read-only access to view compliance data",
    permissions: [
      { resource: "frameworks", actions: ["read"] },
      { resource: "evidence", actions: ["read"] },
      { resource: "policies", actions: ["read"] },
      { resource: "controls", actions: ["read"] },
      { resource: "assessments", actions: ["read"] },
      { resource: "reports", actions: ["read"] },
    ],
  },
  custom: {
    name: "custom",
    description: "Custom role with user-defined permissions",
    permissions: [],
  },
};

export class RBACEngine {
  private roles: Map<RoleName, Role> = new Map();
  private assignments: Map<string, UserRoleAssignment[]> = new Map();
  private tenants: Map<string, TenantConfig> = new Map();
  private auditLog: AuditLogEntry[] = [];
  private config: RBACConfig;

  constructor(config: RBACConfig) {
    this.config = {
      jwtExpiresIn: 3600,
      auditLogLimit: 10000,
      ...config,
    };
    for (const [name, role] of Object.entries(BUILTIN_ROLES)) {
      this.roles.set(name as RoleName, { ...role });
    }
  }

  createTenant(name: string, parentTenantId?: string): TenantConfig {
    const tenant: TenantConfig = {
      id: `tenant-${randomUUID()}`,
      name,
      parentTenantId,
      createdAt: new Date().toISOString(),
      settings: {},
    };
    this.tenants.set(tenant.id, tenant);
    return tenant;
  }

  getTenant(tenantId: string): TenantConfig | undefined {
    return this.tenants.get(tenantId);
  }

  assignRole(
    userId: string,
    role: RoleName,
    scope: ScopeLevel,
    tenantId: string,
    assignedBy: string,
    scopeId?: string
  ): UserRoleAssignment {
    const roleDef = this.roles.get(role);
    if (!roleDef) throw new Error(`Role not found: ${role}`);

    const assignment: UserRoleAssignment = {
      userId,
      role,
      scope,
      scopeId,
      tenantId,
      assignedAt: new Date().toISOString(),
      assignedBy,
    };

    const key = `${userId}:${tenantId}`;
    const existing = this.assignments.get(key) || [];
    existing.push(assignment);
    this.assignments.set(key, existing);

    this.logAudit({
      userId: assignedBy,
      tenantId,
      resource: "roles",
      action: "write",
      allowed: true,
      role: "admin",
      scope: "global",
      reason: `Assigned role ${role} to user ${userId}`,
    });

    return assignment;
  }

  removeRole(userId: string, tenantId: string, role?: RoleName): boolean {
    const key = `${userId}:${tenantId}`;
    const existing = this.assignments.get(key);
    if (!existing) return false;

    if (role) {
      const filtered = existing.filter((a) => a.role !== role);
      this.assignments.set(key, filtered);
      return filtered.length < existing.length;
    }

    return this.assignments.delete(key);
  }

  getUserRoles(userId: string, tenantId: string): UserRoleAssignment[] {
    return this.assignments.get(`${userId}:${tenantId}`) || [];
  }

  defineCustomRole(name: string, permissions: Permission[], description: string): Role {
    const role: Role = { name: "custom", permissions, description };
    this.roles.set(name as RoleName, role);
    return role;
  }

  checkPermission(check: PermissionCheck): PermissionResult {
    const assignments = this.getUserRoles(check.userId, check.tenantId);

    if (assignments.length === 0) {
      const result: PermissionResult = {
        allowed: false,
        role: "viewer",
        scope: "global",
        reason: "No role assignments found",
      };
    this.logAudit({
      ...check,
      ...result,
    });
      return result;
    }

    for (const assignment of assignments) {
      const roleDef = this.roles.get(assignment.role);
      if (!roleDef) continue;

      for (const perm of roleDef.permissions) {
        if (perm.resource === check.resource && perm.actions.includes(check.action)) {
          const scopeValid = this.validateScope(assignment, check.scopeId);
          const result: PermissionResult = {
            allowed: scopeValid,
            role: assignment.role,
            scope: assignment.scope,
            reason: scopeValid
              ? `Granted via role ${assignment.role}`
              : `Insufficient scope: required ${assignment.scope}`,
          };
          this.logAudit({
            ...check,
            ...result,
          });
          return result;
        }
      }
    }

    const result: PermissionResult = {
      allowed: false,
      role: assignments[0].role,
      scope: assignments[0].scope,
      reason: `No matching permission for ${check.resource}:${check.action}`,
    };
    this.logAudit({
      ...check,
      ...result,
    });
    return result;
  }

  hasPermission(
    userId: string,
    tenantId: string,
    resource: Resource,
    action: Action,
    scopeId?: string
  ): boolean {
    return this.checkPermission({ userId, tenantId, resource, action, scopeId }).allowed;
  }

  generateJWT(userId: string, tenantId: string): string {
    const assignments = this.getUserRoles(userId, tenantId);
    const primaryRole = assignments[0]?.role || "viewer";
    const primaryScope = assignments[0]?.scope || "global";
    const scopeId = assignments[0]?.scopeId;

    const permissions: PermissionString[] = [];
    for (const assignment of assignments) {
      const roleDef = this.roles.get(assignment.role);
      if (roleDef) {
        for (const perm of roleDef.permissions) {
          for (const action of perm.actions) {
            const p: PermissionString = `${perm.resource}:${action}`;
            if (!permissions.includes(p)) permissions.push(p);
          }
        }
      }
    }

    const now = Math.floor(Date.now() / 1000);
    const payload: JWTPayload = {
      sub: userId,
      tenant_id: tenantId,
      role: primaryRole,
      scope: primaryScope,
      scope_id: scopeId,
      permissions,
      iat: now,
      exp: now + (this.config.jwtExpiresIn || 3600),
    };

    const header = this.base64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
    const body = this.base64url(JSON.stringify(payload));
    const signature = createHmac("sha256", this.config.jwtSecret)
      .update(`${header}.${body}`)
      .digest("base64url");

    return `${header}.${body}.${signature}`;
  }

  verifyJWT(token: string): JWTPayload | null {
    try {
      const parts = token.split(".");
      if (parts.length !== 3) return null;

      const [header, body, signature] = parts;
      const expectedSig = createHmac("sha256", this.config.jwtSecret)
        .update(`${header}.${body}`)
        .digest("base64url");

      if (signature !== expectedSig) return null;

      const payload = JSON.parse(Buffer.from(body, "base64url").toString()) as JWTPayload;
      if (payload.exp < Math.floor(Date.now() / 1000)) return null;

      return payload;
    } catch {
      return null;
    }
  }

  createMiddleware() {
    return (req: { headers: Record<string, string | undefined>; userId?: string; tenantId?: string },
            res: { status: (code: number) => { json: (body: unknown) => void } },
            next: () => void) => {
      const authHeader = req.headers.authorization;
      if (!authHeader?.startsWith("Bearer ")) {
        res.status(401).json({ error: "Missing or invalid authorization header" });
        return;
      }

      const token = authHeader.slice(7);
      const payload = this.verifyJWT(token);
      if (!payload) {
        res.status(401).json({ error: "Invalid or expired token" });
        return;
      }

      req.userId = payload.sub;
      req.tenantId = payload.tenant_id;
      next();
    };
  }

  requirePermission(resource: Resource, action: Action) {
    return (req: { userId?: string; tenantId?: string },
            res: { status: (code: number) => { json: (body: unknown) => void } },
            next: () => void) => {
      if (!req.userId || !req.tenantId) {
        res.status(401).json({ error: "Not authenticated" });
        return;
      }

      const result = this.checkPermission({
        userId: req.userId,
        tenantId: req.tenantId,
        resource,
        action,
      });

      if (!result.allowed) {
        res.status(403).json({
          error: "Insufficient permissions",
          reason: result.reason,
          required: `${resource}:${action}`,
        });
        return;
      }

      next();
    };
  }

  getAuditLog(tenantId?: string, limit?: number): AuditLogEntry[] {
    let logs = tenantId
      ? this.auditLog.filter((l) => l.tenantId === tenantId)
      : this.auditLog;
    const max = limit || this.config.auditLogLimit || 1000;
    return logs.slice(-max);
  }

  getRolePermissions(roleName: RoleName): Permission[] {
    return this.roles.get(roleName)?.permissions || [];
  }

  getAllRoles(): Role[] {
    return Array.from(this.roles.values());
  }

  private validateScope(assignment: UserRoleAssignment, requestedScopeId?: string): boolean {
    if (assignment.scope === "global") return true;
    if (assignment.scope === "entity") {
      if (!assignment.scopeId) return true;
      return !requestedScopeId || assignment.scopeId === requestedScopeId;
    }
    if (assignment.scope === "department") {
      if (!assignment.scopeId) return true;
      return !requestedScopeId || assignment.scopeId === requestedScopeId;
    }
    return false;
  }

  private logAudit(entry: Omit<AuditLogEntry, "id" | "timestamp">): void {
    const logEntry: AuditLogEntry = {
      id: `audit-${randomUUID()}`,
      timestamp: new Date().toISOString(),
      ...entry,
    };
    this.auditLog.push(logEntry);
    if (this.auditLog.length > (this.config.auditLogLimit || 10000)) {
      this.auditLog = this.auditLog.slice(-((this.config.auditLogLimit || 10000) / 2));
    }
  }

  private base64url(data: string): string {
    return Buffer.from(data)
      .toString("base64")
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
  }
}
