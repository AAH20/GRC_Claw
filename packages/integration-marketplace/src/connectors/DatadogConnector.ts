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
    id: "dd-monitors",
    name: "Monitors",
    description: "Fetch Datadog monitor configurations and alert states",
    evidenceCategories: ["monitoring", "configuration"],
  },
  {
    id: "dd-alerts",
    name: "Alerts",
    description: "Fetch triggered alerts and alert rule configurations",
    evidenceCategories: ["monitoring", "incident_detection"],
  },
  {
    id: "dd-apm",
    name: "APM Configurations",
    description: "Fetch APM service configurations and security tracking",
    evidenceCategories: ["application_security", "monitoring"],
  },
];

export class DatadogConnector implements IntegrationConnector {
  readonly id = "datadog";
  readonly name = "Datadog";
  readonly category = "monitoring" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string,
    method = "GET"
  ): Promise<Record<string, unknown>> {
    const site = config.extra?.site || "datadoghq.com";
    const base = `https://api.${site}`;
    const resp = await fetch(`${base}${endpoint}`, {
      method,
      headers: {
        "DD-API-KEY": config.apiToken || "",
        "DD-APPLICATION-KEY": config.extra?.appKey || "",
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Datadog API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/v1/validate");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const monitors = await this.fetchApi(config, "/api/v1/monitor");
    const monitorList = Array.isArray(monitors) ? monitors : [];
    const activeMonitors = monitorList.filter(
      (m: Record<string, unknown>) => m.overall_state === "OK"
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "dd-monitors",
      timestamp: now,
      hash: hashEvidence({ monitorCount: monitorList.length }),
      framework: "SOC2",
      controlId: "CC7.1",
      source: "datadog/monitors",
      status: monitorList.length > 0 ? "compliant" : "non_compliant",
      data: {
        totalMonitors: monitorList.length,
        activeMonitors: activeMonitors.length,
        alertMonitors: monitorList.length - activeMonitors.length,
      },
      metadata: { site: config.extra?.site || "datadoghq.com" },
    });

    const alerts = await this.fetchApi(config, "/api/v1/alerts").catch(() => []);
    const alertList = Array.isArray(alerts) ? alerts : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "dd-alerts",
      timestamp: now,
      hash: hashEvidence({ alertCount: alertList.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "datadog/alerts",
      status: "unknown",
      data: { alertRuleCount: alertList.length },
      metadata: { site: config.extra?.site || "datadoghq.com" },
    });

    const services = await this.fetchApi(config, "/api/v1/services").catch(() => ({
      services: [],
    }));
    const serviceList = (services.services || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "dd-apm",
      timestamp: now,
      hash: hashEvidence({ serviceCount: serviceList.length }),
      framework: "ISO27001",
      controlId: "A.12.4.1",
      source: "datadog/services",
      status: "unknown",
      data: { serviceCount: serviceList.length },
      metadata: { site: config.extra?.site || "datadoghq.com" },
    });

    return artifacts;
  }
}
