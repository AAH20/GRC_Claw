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
    id: "carbonblack-endpoints",
    name: "Endpoint Protection",
    description: "Fetch Carbon Black sensor status and policy assignments",
    evidenceCategories: ["endpoint", "monitoring"],
  },
  {
    id: "carbonblack-alerts",
    name: "Security Alerts",
    description: "Fetch alert severity and investigation status",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "carbonblack-policies",
    name: "Response Policies",
    description: "Fetch prevention and response policy configurations",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "carbonblack-live-response",
    name: "Live Response",
    description: "Fetch live response session logs and forensics",
    evidenceCategories: ["monitoring", "change_management"],
  },
];

export class CarbonBlackConnector implements IntegrationConnector {
  readonly id = "carbonblack";
  readonly name = "VMware Carbon Black";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://defense.conferdeploy.net";
    const resp = await fetch(`${base}/api/v6${endpoint}`, {
      headers: {
        "X-Auth-Token": config.apiToken || "",
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Carbon Black API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/apps/search");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const sensors = await this.fetchApi(config, "/sensors").catch(() => ({ results: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "carbonblack-endpoints",
      timestamp: now,
      hash: hashEvidence(sensors),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "carbonblack/sensors",
      status: (sensors.results as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { sensorCount: (sensors.results as unknown[])?.length || 0 },
      metadata: {},
    });

    const alerts = await this.fetchApi(config, "/alerts/search").catch(() => ({ results: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "carbonblack-alerts",
      timestamp: now,
      hash: hashEvidence(alerts),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "carbonblack/alerts",
      status: (alerts.results as unknown[])?.length === 0 ? "compliant" : "non_compliant",
      data: { openAlerts: (alerts.results as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
