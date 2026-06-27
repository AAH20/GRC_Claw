import type {
  IntegrationConnector,
  ConnectorConfig,
  EvidenceArtifact,
  IntegrationCapability,
  ComplianceFramework,
} from "../types.js";
import { hashEvidence, generateEvidenceId } from "../types.js";

const capabilities: IntegrationCapability[] = [
  {
    id: "auth0-users",
    name: "User Accounts",
    description: "Fetch Auth0 user accounts, email verification, and MFA enrollment status",
    evidenceCategories: ["identity_management", "authentication"],
  },
  {
    id: "auth0-applications",
    name: "Applications",
    description: "Fetch registered applications and their OAuth/OIDC configurations",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "auth0-connections",
    name: "Connections",
    description: "Fetch identity provider connections and their configurations",
    evidenceCategories: ["identity_management", "configuration"],
  },
  {
    id: "auth0-attack-protection",
    name: "Attack Protection",
    description: "Fetch Auth0 attack protection settings (brute force, suspicious IP, etc.)",
    evidenceCategories: ["security_controls", "threat_protection"],
  },
  {
    id: "auth0-roles",
    name: "Roles & Permissions",
    description: "Fetch assigned roles, permissions, and API authorizations",
    evidenceCategories: ["access_control", "authorization"],
  },
];

export class Auth0Connector implements IntegrationConnector {
  readonly id = "auth0";
  readonly name = "Auth0";
  readonly category = "identity" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const domain = config.extra?.domain || config.baseUrl || "";
    const base = domain.startsWith("http") ? domain : `https://${domain}`;
    const resp = await fetch(`${base}/api/v2${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Auth0 API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/users?per_page=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const users = await this.fetchApi(config, "/users?per_page=100&include_totals=true").catch(() => ({ users: [], total: 0 }));
    const userList = (users.users || []) as Record<string, unknown>[];
    const mfaEnabled = userList.filter((u) => {
      const factors = (u.multifactor || []) as unknown[];
      return factors.length > 0;
    });
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "auth0-users",
      timestamp: now,
      hash: hashEvidence({ total: userList.length, mfaEnabled: mfaEnabled.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "auth0/users",
      status: mfaEnabled.length > userList.length * 0.8 ? "compliant" : "partial",
      data: {
        userCount: userList.length,
        mfaEnabledCount: mfaEnabled.length,
        total: users.total,
      },
      metadata: { domain: config.extra?.domain || "" },
    });

    const apps = await this.fetchApi(config, "/clients?is_global=false&fields=name,app_type,callbacks").catch(() => ({ clients: [] }));
    const appList = (apps.clients || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "auth0-applications",
      timestamp: now,
      hash: hashEvidence({ appCount: appList.length }),
      framework: "ISO27001",
      controlId: "A.14.2.5",
      source: "auth0/clients",
      status: "unknown",
      data: { appCount: appList.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    const connections = await this.fetchApi(config, "/connections?strategy=auth0,discord,facebook,google-oauth2,linkedin,samlp,oidc").catch(() => ({ connections: [] }));
    const connList = (connections.connections || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "auth0-connections",
      timestamp: now,
      hash: hashEvidence({ connectionCount: connList.length }),
      framework: "SOC2",
      controlId: "CC6.2",
      source: "auth0/connections",
      status: "unknown",
      data: { connectionCount: connList.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    const attackProtection = await this.fetchApi(config, "/attack-protection").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "auth0-attack-protection",
      timestamp: now,
      hash: hashEvidence(attackProtection),
      framework: "NIST_CSF",
      controlId: "PR.AC-1",
      source: "auth0/attack-protection",
      status: "unknown",
      data: { attackProtection },
      metadata: { domain: config.extra?.domain || "" },
    });

    const roles = await this.fetchApi(config, "/roles").catch(() => ({ roles: [] }));
    const roleList = (roles.roles || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "auth0-roles",
      timestamp: now,
      hash: hashEvidence({ roleCount: roleList.length }),
      framework: "ISO27001",
      controlId: "A.9.2.3",
      source: "auth0/roles",
      status: "unknown",
      data: { roleCount: roleList.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    return artifacts;
  }
}
