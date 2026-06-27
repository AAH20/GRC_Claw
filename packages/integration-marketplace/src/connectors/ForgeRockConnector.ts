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
    id: "forgerock-realms",
    name: "Realm Configuration",
    description: "Fetch authentication realms and chain configurations",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "forgerock-policies",
    name: "Authorization Policies",
    description: "Fetch policy decisions and access rules",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "forgerock-tokens",
    name: "Session Tokens",
    description: "Fetch token issuance and session management",
    evidenceCategories: ["access_control", "monitoring"],
  },
  {
    id: "forgerock-audit",
    name: "Access Audit",
    description: "Fetch authentication and authorization audit logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class ForgeRockConnector implements IntegrationConnector {
  readonly id = "forgerock";
  readonly name = "ForgeRock";
  readonly category = "identity" as const;
  readonly authType = "api_key" as const;
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
    const base = config.baseUrl || "https://forgerock.example.com";
    const resp = await fetch(`${base}/openam/json${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
        "Accept-API-Version": "resource=2.1",
      },
    });
    if (!resp.ok) throw new Error(`ForgeRock API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/realms");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const realms = await this.fetchApi(config, "/realms").catch(() => ({ realmNames: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "forgerock-realms",
      timestamp: now,
      hash: hashEvidence(realms),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "forgerock/realms",
      status: (realms.realmNames as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { realmCount: (realms.realmNames as unknown[])?.length || 0 },
      metadata: {},
    });

    const policies = await this.fetchApi(config, "/policies").catch(() => ({ result: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "forgerock-policies",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "forgerock/policies",
      status: (policies.result as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { policyCount: (policies.result as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
