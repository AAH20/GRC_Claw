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
    id: "opsgenie-incidents",
    name: "Incident Management",
    description: "Fetch Opsgenie incident timelines, escalation policies, and SLA metrics",
    evidenceCategories: ["incident_management", "monitoring"],
  },
  {
    id: "opsgenie-schedules",
    name: "On-Call Schedules",
    description: "Fetch on-call schedules, rotations, and escalation handoff records",
    evidenceCategories: ["incident_management", "configuration"],
  },
  {
    id: "opsgenie-integrations",
    name: "Alert Integrations",
    description: "Fetch Opsgenie alert integration configurations and forwarding rules",
    evidenceCategories: ["configuration", "monitoring"],
  },
];

export class OpsgenieConnector implements IntegrationConnector {
  readonly id = "opsgenie";
  readonly name = "Opsgenie";
  readonly category = "incident_management" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.opsgenie.com/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `GenieKey ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Opsgenie API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/account");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const alerts = await this.fetchApi(config, "/alerts?limit=100").catch(() => ({ data: [] }));
    const alertList = (alerts.data || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "opsgenie-incidents",
      timestamp: now,
      hash: hashEvidence({ alertCount: alertList.length }),
      framework: "SOC2",
      controlId: "CC7.3",
      source: "opsgenie/alerts",
      status: "unknown",
      data: { openAlerts: alertList.length },
      metadata: {},
    });

    return artifacts;
  }
}
