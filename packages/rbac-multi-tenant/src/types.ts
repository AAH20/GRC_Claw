export type RoleName =
  | "admin"
  | "compliance_officer"
  | "auditor"
  | "viewer"
  | "custom";

export type ScopeLevel = "global" | "entity" | "department";

export type Resource =
  | "frameworks"
  | "evidence"
  | "policies"
  | "controls"
  | "assessments"
  | "vendors"
  | "risks"
  | "incidents"
  | "connectors"
  | "users"
  | "roles"
  | "tenants"
  | "audit_logs"
  | "reports"
  | "settings";

export type Action =
  | "read"
  | "write"
  | "delete"
  | "approve"
  | "export"
  | "manage";

export type PermissionString = `${Resource}:${Action}`;

export interface Permission {
  resource: Resource;
  actions: Action[];
}

export interface Role {
  name: RoleName;
  permissions: Permission[];
  description: string;
}

export interface UserRoleAssignment {
  userId: string;
  role: RoleName;
  scope: ScopeLevel;
  scopeId?: string;
  tenantId: string;
  assignedAt: string;
  assignedBy: string;
}

export interface TenantConfig {
  id: string;
  name: string;
  parentTenantId?: string;
  createdAt: string;
  settings: Record<string, unknown>;
}

export interface PermissionCheck {
  userId: string;
  tenantId: string;
  resource: Resource;
  action: Action;
  scopeId?: string;
}

export interface PermissionResult {
  allowed: boolean;
  role: RoleName;
  scope: ScopeLevel;
  reason: string;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  userId: string;
  tenantId: string;
  resource: Resource;
  action: Action;
  allowed: boolean;
  role: RoleName;
  scope: ScopeLevel;
  reason: string;
  metadata?: Record<string, unknown>;
}

export interface JWTPayload {
  sub: string;
  tenant_id: string;
  role: RoleName;
  scope: ScopeLevel;
  scope_id?: string;
  permissions: PermissionString[];
  iat: number;
  exp: number;
}

export interface RBACConfig {
  jwtSecret: string;
  jwtExpiresIn?: number;
  auditLogLimit?: number;
}
