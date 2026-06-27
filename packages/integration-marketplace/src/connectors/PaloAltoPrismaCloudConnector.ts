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
    id: "prisma-cloud-compliance",
    name: "Cloud Compliance posture",
    description: "Fetch cloud compliance posture and misconfiguration alerts",
    evidenceCategories: ["vulnerability_management", "configuration"],
  },
  {
    id: "prisma-cloud-audit",
    name: "Audit Logs",
    description: "Fetch cloud audit logs and API activity",
    evidenceCategories: ["access_control", "monitoring"],
  },
  {
    id: "prisma-cloud-runtime",
    name: "Runtime Protection",
    description: "Fetch runtime protection policies and alerts",
    evidenceCategories: ["vulnerability_management", "data_protection"],
  },
  {
    id: "prisma-cloud-network",
    name: "Network Security",
    description: "Fetch network segmentation and firewall rules",
    evidenceCategories: ["access_control", "configuration"],
  },
];

export class PaloAltoPrismaCloudConnector implements IntegrationConnector {
  readonly id = "palo-alto-prisma-cloud";
  readonly name = "Palo Alto Prisma Cloud";
  readonly category = "cloud_provider" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
    "HIPAA",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.prismacloud.io";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Prisma Cloud API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/v1/alert");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const cloudType = config.extra?.cloudType || "aws";

    const compliance = await this.fetchApi(
      config,
      `/api/v1/compliance?cloudType=${cloudType}`
    ).catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "prisma-cloud-compliance",
      timestamp: now,
      hash: hashEvidence(compliance),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `prismacloud.io/${cloudType}/compliance`,
      status: (compliance.items as unknown[])?.length === 0 ? "compliant" : "partial",
      data: { complianceIssues: (compliance.items as unknown[])?.length || 0 },
      metadata: { cloudType },
    });

    const alerts = await this.fetchApi(
      config,
      `/api/v1/alert?status=open&limit=10`
    ).catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "prisma-cloud-audit",
      timestamp: now,
      hash: hashEvidence(alerts),
      framework: "ISO27001",
      controlId: "A.12.4.1",
      source: `prismacloud.io/${cloudType}/alerts`,
      status: (alerts.items as unknown[])?.length === 0 ? "compliant" : "non_compliant",
      data: { openAlerts: (alerts.items as unknown[])?.length || 0 },
      metadata: { cloudType },
    });

    const network = await this.fetchApi(
      config,
      `/api/v1/network/firewall?cloudType=${cloudType}`
    ).catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "prisma-cloud-network",
      timestamp: now,
      hash: hashEvidence(network),
      framework: "NIST_CSF",
      controlId: "PR.AC-5",
      source: `prismacloud.io/${cloudType}/network`,
      status: "partial",
      data: { firewallRules: (network.items as unknown[])?.length || 0 },
      metadata: { cloudType },
    });

    return artifacts;
  }
}
