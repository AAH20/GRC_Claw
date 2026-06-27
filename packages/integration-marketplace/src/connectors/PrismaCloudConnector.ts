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
    id: "prisma-alerts",
    name: "Security Alerts",
    description: "Fetch Prisma Cloud security alerts and policy violations",
    evidenceCategories: ["vulnerability_management", "threat_detection"],
  },
  {
    id: "prisma-compliance",
    name: "Compliance Reports",
    description: "Fetch compliance posture across cloud accounts and frameworks",
    evidenceCategories: ["compliance", "configuration"],
  },
  {
    id: "prisma-cloud-assets",
    name: "Cloud Asset Inventory",
    description: "Fetch discovered cloud assets and misconfigurations",
    evidenceCategories: ["asset_management", "configuration"],
  },
  {
    id: "prisma-network",
    name: "Network Security",
    description: "Fetch network exposure and security group findings",
    evidenceCategories: ["network_security", "configuration"],
  },
];

export class PrismaCloudConnector implements IntegrationConnector {
  readonly id = "prisma_cloud";
  readonly name = "Prisma Cloud";
  readonly category = "cloud_provider" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
    "HIPAA",
    "CIS",
  ];

  private async getToken(config: ConnectorConfig): Promise<string> {
    const base = config.baseUrl || "https://api.prismacloud.io";
    const resp = await fetch(`${base}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: config.clientId,
        password: config.clientSecret,
      }),
    });
    const data = (await resp.json()) as Record<string, unknown>;
    return data.token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getToken(config);
      const base = config.baseUrl || "https://api.prismacloud.io";
      const resp = await fetch(`${base}/api/v1/policy`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return resp.ok;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const token = await this.getToken(config);
    const base = config.baseUrl || "https://api.prismacloud.io";
    const headers = { Authorization: `Bearer ${token}` };
    const cloudAccount = config.extra?.cloudAccount || "default";

    const alerts = await fetch(
      `${base}/api/v1/alert?timeRange.amount=7&timeRange.unit=day&status=open`,
      { headers }
    )
      .then((r) => r.json())
      .catch(() => ({ items: [] }));
    const alertItems = Array.isArray(alerts.items) ? alerts.items : [];
    const criticalAlerts = alertItems.filter(
      (a: Record<string, unknown>) => a.severity === "high" || a.severity === "critical"
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "prisma-alerts",
      timestamp: now,
      hash: hashEvidence({ count: alertItems.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: `prisma/${cloudAccount}/alerts`,
      status: criticalAlerts.length === 0 ? "compliant" : "non_compliant",
      data: { totalAlerts: alertItems.length, criticalHigh: criticalAlerts.length },
      metadata: { cloudAccount },
    });

    const compliance = await fetch(
      `${base}/api/v1/compliance/posture?cloudType=aws,azure,gcp`,
      { headers }
    )
      .then((r) => r.json())
      .catch(() => ({ items: [] }));
    const compItems = Array.isArray(compliance.items) ? compliance.items : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "prisma-compliance",
      timestamp: now,
      hash: hashEvidence({ count: compItems.length }),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: `prisma/${cloudAccount}/compliance`,
      status: compItems.length > 0 ? "compliant" : "partial",
      data: { complianceStandards: compItems.length },
      metadata: { cloudAccount },
    });

    const assets = await fetch(
      `${base}/api/v1/resource?cloudType=aws,azure,gcp&limit=100`,
      { headers }
    )
      .then((r) => r.json())
      .catch(() => ({ items: [] }));
    const assetItems = Array.isArray(assets.items) ? assets.items : [];
    const misconfigured = assetItems.filter(
      (a: Record<string, unknown>) => a.hasMisconfig === true
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "prisma-cloud-assets",
      timestamp: now,
      hash: hashEvidence({ count: assetItems.length }),
      framework: "NIST_CSF",
      controlId: "ID.AM",
      source: `prisma/${cloudAccount}/assets`,
      status: misconfigured.length === 0 ? "compliant" : "non_compliant",
      data: { totalAssets: assetItems.length, misconfigured: misconfigured.length },
      metadata: { cloudAccount },
    });

    const network = await fetch(
      `${base}/api/v1/network/vpc?limit=50`,
      { headers }
    )
      .then((r) => r.json())
      .catch(() => ({ items: [] }));
    const networkItems = Array.isArray(network.items) ? network.items : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "prisma-network",
      timestamp: now,
      hash: hashEvidence({ count: networkItems.length }),
      framework: "PCI_DSS",
      controlId: "1.2.1",
      source: `prisma/${cloudAccount}/network`,
      status: "compliant",
      data: { vpcCount: networkItems.length },
      metadata: { cloudAccount },
    });

    return artifacts;
  }
}
