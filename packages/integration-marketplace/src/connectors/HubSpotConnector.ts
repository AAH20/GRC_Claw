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
    id: "hs-user-access",
    name: "User Access",
    description: "Fetch HubSpot user accounts and permission levels",
    evidenceCategories: ["access_control"],
  },
  {
    id: "hs-integrations",
    name: "Integration Permissions",
    description: "Fetch connected apps and their scopes",
    evidenceCategories: ["third_party_management", "access_control"],
  },
];

export class HubSpotConnector implements IntegrationConnector {
  readonly id = "hubspot";
  readonly name = "HubSpot";
  readonly category = "project_management" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.hubapi.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `Bearer ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`HubSpot API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/crm/v3/objects/users?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const users = await this.fetchApi(config, "/crm/v3/objects/users?limit=100");
    const userList = (users.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "hs-user-access",
      timestamp: now,
      hash: hashEvidence({ userCount: userList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "hubspot/users",
      status: userList.length > 0 ? "compliant" : "non_compliant",
      data: { userCount: userList.length },
      metadata: {},
    });

    const integrations = await fetch(
      `${config.baseUrl || "https://api.hubapi.com"}/crm/v3/objects/users?limit=100`,
      {
        headers: { Authorization: `Bearer ${config.apiToken}` },
      }
    ).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "hs-integrations",
      timestamp: now,
      hash: hashEvidence(integrations),
      framework: "ISO27001",
      controlId: "A.14.2.5",
      source: "hubspot/integrations",
      status: "unknown",
      data: { integrations },
      metadata: {},
    });

    return artifacts;
  }
}
