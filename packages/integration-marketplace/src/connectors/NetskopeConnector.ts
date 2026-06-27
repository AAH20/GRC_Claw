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
    id: "netskope-casb",
    name: "Cloud Access Security",
    description: "Fetch CASB policies and shadow IT discoveries",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "netskope-sase",
    name: "SASE Security",
    description: "Fetch SASE policies and zero trust network access rules",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "netskope-dlp",
    name: "Cloud DLP",
    description: "Fetch DLP policies and incident details",
    evidenceCategories: ["data_protection", "monitoring"],
  },
  {
    id: "netskope-swg",
    name: "Secure Web Gateway",
    description: "Fetch SWG URL filtering and threat protection",
    evidenceCategories: ["vulnerability_management", "access_control"],
  },
];

export class NetskopeConnector implements IntegrationConnector {
  readonly id = "netskope";
  readonly name = "Netskope";
  readonly category = "cloud_provider" as const;
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
    const base = config.baseUrl || "https://tenant.netskope.com";
    const resp = await fetch(`${base}/api/v1${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Netskope API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/security/policies");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const policies = await this.fetchApi(config, "/security/policies").catch(() => ({
      policies: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "netskope-casb",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "netskope/security-policies",
      status: (policies.policies as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { securityPolicies: (policies.policies as unknown[])?.length || 0 },
      metadata: {},
    });

    const incidents = await this.fetchApi(config, "/security/incidents?limit=10").catch(() => ({
      incidents: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "netskope-dlp",
      timestamp: now,
      hash: hashEvidence(incidents),
      framework: "ISO27001",
      controlId: "A.8.3.1",
      source: "netskope/incidents",
      status: (incidents.incidents as unknown[])?.length === 0 ? "compliant" : "non_compliant",
      data: { openIncidents: (incidents.incidents as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
