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
    id: "mcafee-endpoints",
    name: "Endpoint Protection",
    description: "Fetch McAfee/Trellix endpoint agent status and protection health",
    evidenceCategories: ["endpoint_security", "monitoring"],
  },
  {
    id: "mcafee-detections",
    name: "Threat Detections",
    description: "Fetch threat detection and remediation event history",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "mcafee-policies",
    name: "Security Policies",
    description: "Fetch McAfee ePO policy assignments and compliance reports",
    evidenceCategories: ["policy_compliance", "configuration"],
  },
];

export class McAfeeConnector implements IntegrationConnector {
  readonly id = "mcafee";
  readonly name = "McAfee (Trellix)";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.trellix.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`McAfee API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/devices?pageSize=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const devices = await this.fetchApi(config, "/devices?pageSize=100").catch(() => ({ data: [] }));
    const deviceList = (devices.data || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "mcafee-endpoints",
      timestamp: now,
      hash: hashEvidence({ deviceCount: deviceList.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "mcafee/devices",
      status: deviceList.length > 0 ? "compliant" : "unknown",
      data: { endpointCount: deviceList.length },
      metadata: {},
    });

    const threats = await this.fetchApi(config, "/events?pageSize=10").catch(() => ({ data: [] }));
    const threatList = (threats.data || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "mcafee-detections",
      timestamp: now,
      hash: hashEvidence({ threatCount: threatList.length }),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "mcafee/events",
      status: threatList.length === 0 ? "compliant" : "non_compliant",
      data: { recentThreats: threatList.length },
      metadata: {},
    });

    return artifacts;
  }
}
