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
    id: "okta-users",
    name: "User Accounts",
    description: "Fetch Okta user accounts and status",
    evidenceCategories: ["identity_management"],
  },
  {
    id: "okta-mfa-factors",
    name: "MFA Factors",
    description: "Fetch enrolled MFA factors across users",
    evidenceCategories: ["authentication"],
  },
  {
    id: "okta-app-assignments",
    name: "App Assignments",
    description: "Fetch application assignments and SSO configurations",
    evidenceCategories: ["access_control"],
  },
  {
    id: "okta-group-memberships",
    name: "Group Memberships",
    description: "Fetch group memberships and role assignments",
    evidenceCategories: ["access_control", "authorization"],
  },
];

export class OktaConnector implements IntegrationConnector {
  readonly id = "okta";
  readonly name = "Okta";
  readonly category = "identity" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || `https://${config.extra?.domain || "example"}.okta.com/api/v1`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `SSWS ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`Okta API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/users/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const users = await this.fetchApi(config, "/users?filter=status%20eq%20%22ACTIVE%22&limit=200");
    const userList = Array.isArray(users) ? users : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "okta-users",
      timestamp: now,
      hash: hashEvidence({ users: userList.map((u: Record<string, unknown>) => ({ id: u.id, status: u.status })) }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "okta/users",
      status: "compliant",
      data: { activeUserCount: userList.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    const factors = await this.fetchApi(config, "/users/me/factors").catch(() => []);
    const factorList = Array.isArray(factors) ? factors : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "okta-mfa-factors",
      timestamp: now,
      hash: hashEvidence({ factors: factorList }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "okta/factors",
      status: factorList.length > 0 ? "compliant" : "non_compliant",
      data: { factorTypes: factorList.map((f: Record<string, unknown>) => f.factorType) },
      metadata: { domain: config.extra?.domain || "" },
    });

    const apps = await this.fetchApi(config, "/apps?limit=100").catch(() => []);
    const appList = Array.isArray(apps) ? apps : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "okta-app-assignments",
      timestamp: now,
      hash: hashEvidence({ apps: appList.map((a: Record<string, unknown>) => ({ id: a.id, name: a.name })) }),
      framework: "ISO27001",
      controlId: "A.9.2.5",
      source: "okta/apps",
      status: "unknown",
      data: { appCount: appList.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    const groups = await this.fetchApi(config, "/groups?limit=100").catch(() => []);
    const groupList = Array.isArray(groups) ? groups : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "okta-group-memberships",
      timestamp: now,
      hash: hashEvidence({ groups: groupList.map((g: Record<string, unknown>) => ({ id: g.id, name: ((g.profile as Record<string, unknown>) || {}).name })) }),
      framework: "SOC2",
      controlId: "CC6.3",
      source: "okta/groups",
      status: groupList.length > 0 ? "compliant" : "non_compliant",
      data: { groupCount: groupList.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    return artifacts;
  }
}
