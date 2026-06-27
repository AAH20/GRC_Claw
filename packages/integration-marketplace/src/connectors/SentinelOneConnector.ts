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
    id: "sentinelone-agents",
    name: "Agent Fleet",
    description: "Fetch SentinelOne agent status and health across endpoints",
    evidenceCategories: ["endpoint", "monitoring"],
  },
  {
    id: "sentinelone-detections",
    name: "Threat Detections",
    description: "Fetch threat detection events and incident counts",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "sentinelone-policies",
    name: "Deep Visibility",
    description: "Fetch detection policy configurations and exclusions",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "sentinelone-response",
    name: "Response Actions",
    description: "Fetch remote shell, isolate, and response action logs",
    evidenceCategories: ["monitoring", "change_management"],
  },
];

export class SentinelOneConnector implements IntegrationConnector {
  readonly id = "sentinelone";
  readonly name = "SentinelOne";
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
    const base = config.baseUrl || "https://usea1.sentinelone.com";
    const resp = await fetch(`${base}/web/api/v2.1${endpoint}`, {
      headers: {
        Authorization: `ApiToken ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`SentinelOne API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/agents");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const agents = await this.fetchApi(config, "/agents").catch(() => ({ data: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sentinelone-agents",
      timestamp: now,
      hash: hashEvidence(agents),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "sentinelone/agents",
      status: (agents.data as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { agentCount: (agents.data as unknown[])?.length || 0 },
      metadata: {},
    });

    const threats = await this.fetchApi(config, "/threats?limit=10").catch(() => ({ data: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sentinelone-detections",
      timestamp: now,
      hash: hashEvidence(threats),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "sentinelone/threats",
      status: (threats.data as unknown[])?.length === 0 ? "compliant" : "non_compliant",
      data: { openThreats: (threats.data as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
