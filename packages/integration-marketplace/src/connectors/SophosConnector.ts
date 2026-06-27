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
    id: "sophos-endpoints",
    name: "Endpoint Protection",
    description: "Fetch Sophos endpoint agent status and managed status",
    evidenceCategories: ["endpoint_security", "monitoring"],
  },
  {
    id: "sophos-threats",
    name: "Threat Detections",
    description: "Fetch threat detection events and incident summaries",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "sophos-policies",
    name: "Security Policies",
    description: "Fetch Sophos security policy configurations and compliance state",
    evidenceCategories: ["policy_compliance", "configuration"],
  },
];

export class SophosConnector implements IntegrationConnector {
  readonly id = "sophos";
  readonly name = "Sophos";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const tenantId = config.tenantId || config.extra?.tenantId || "";
    const base = config.baseUrl || `https://api-${tenantId}.central.sophos.com`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
      },
    });
    if (!resp.ok) throw new Error(`Sophos API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/endpoint/v1/endpoints?pageSize=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const endpoints = await this.fetchApi(
      config,
      "/endpoint/v1/endpoints?pageSize=100"
    ).catch(() => ({ items: [] }));
    const endpointList = (endpoints.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sophos-endpoints",
      timestamp: now,
      hash: hashEvidence({ endpointCount: endpointList.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "sophos/endpoints",
      status: endpointList.length > 0 ? "compliant" : "unknown",
      data: { endpointCount: endpointList.length },
      metadata: {},
    });

    const detections = await this.fetchApi(
      config,
      "/detector/v2/detections?pageSize=10"
    ).catch(() => ({ items: [] }));
    const detectList = (detections.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sophos-threats",
      timestamp: now,
      hash: hashEvidence({ detectionCount: detectList.length }),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "sophos/detections",
      status: detectList.length === 0 ? "compliant" : "non_compliant",
      data: { recentDetections: detectList.length },
      metadata: {},
    });

    return artifacts;
  }
}
