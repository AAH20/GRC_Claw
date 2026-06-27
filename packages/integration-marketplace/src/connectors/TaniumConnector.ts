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
    id: "tanium-endpoints",
    name: "Endpoint Inventory",
    description: "Fetch Tanium endpoint count and compliance status",
    evidenceCategories: ["endpoint", "monitoring"],
  },
  {
    id: "tanium-policies",
    name: "Compliance Policies",
    description: "Fetch compliance policy rules and violation counts",
    evidenceCategories: ["compliance", "monitoring"],
  },
  {
    id: "tanium-patches",
    name: "Patch Status",
    description: "Fetch endpoint patch compliance and missing updates",
    evidenceCategories: ["vulnerability_management", "endpoint"],
  },
  {
    id: "tanium-packages",
    name: "Threat Response",
    description: "Fetch threat detection packages and response actions",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
];

export class TaniumConnector implements IntegrationConnector {
  readonly id = "tanium";
  readonly name = "Tanium";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "PCI_DSS",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://tanium.example.com";
    const resp = await fetch(`${base}/api/v2${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Tanium API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/version");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const endpoints = await this.fetchApi(config, "/endpoints?count=1").catch(() => ({
      totalRecords: 0,
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tanium-endpoints",
      timestamp: now,
      hash: hashEvidence(endpoints),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "tanium/endpoints",
      status: (endpoints.totalRecords as number) > 0 ? "compliant" : "unknown",
      data: { endpointCount: endpoints.totalRecords },
      metadata: {},
    });

    const packages = await this.fetchApi(config, "/packages").catch(() => ({ data: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tanium-packages",
      timestamp: now,
      hash: hashEvidence(packages),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "tanium/packages",
      status: (packages.data as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { activePackages: (packages.data as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
