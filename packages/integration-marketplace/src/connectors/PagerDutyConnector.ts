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
    id: "pagerduty-incidents-v2",
    name: "Incident Management",
    description: "Fetch PagerDuty incident lifecycle, escalation policies, and SLA compliance",
    evidenceCategories: ["incident_management", "availability"],
  },
  {
    id: "pagerduty-oncall-v2",
    name: "On-Call Schedules",
    description: "Fetch on-call schedules, rotations, and escalation handoff records",
    evidenceCategories: ["incident_management", "configuration"],
  },
  {
    id: "pagerduty-services-v2",
    name: "Service Catalog",
    description: "Fetch PagerDuty service health, integrations, and business impact mapping",
    evidenceCategories: ["incident_management", "monitoring"],
  },
];

export class PagerDutyConnector implements IntegrationConnector {
  readonly id = "pagerduty";
  readonly name = "PagerDuty";
  readonly category = "incident_management" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.pagerduty.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Token token=${config.apiToken}`,
        Accept: "application/vnd.pagerduty+json;version=2",
      },
    });
    if (!resp.ok) throw new Error(`PagerDuty API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/users/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const services = await this.fetchApi(config, "/services?limit=100");
    const serviceList = (services.services || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "pagerduty-services-v2",
      timestamp: now,
      hash: hashEvidence({ services: serviceList.map((s) => ({ id: s.id, name: s.name })) }),
      framework: "SOC2",
      controlId: "CC7.3",
      source: "pagerduty/services",
      status: serviceList.length > 0 ? "compliant" : "non_compliant",
      data: { serviceCount: serviceList.length },
      metadata: {},
    });

    const schedules = await this.fetchApi(config, "/schedules?limit=100").catch(() => ({
      schedules: [],
    }));
    const scheduleList = (schedules.schedules || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "pagerduty-oncall-v2",
      timestamp: now,
      hash: hashEvidence({ schedules: scheduleList.map((s) => ({ id: s.id, name: s.name })) }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "pagerduty/schedules",
      status: scheduleList.length > 0 ? "compliant" : "non_compliant",
      data: { scheduleCount: scheduleList.length },
      metadata: {},
    });

    const since = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
    const incidents = await this.fetchApi(
      config,
      `/incidents?since=${since}&limit=100&statuses[]=triggered&statuses[]=resolved`
    ).catch(() => ({ incidents: [] }));
    const incidentList = (incidents.incidents || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "pagerduty-incidents-v2",
      timestamp: now,
      hash: hashEvidence({ incidents: incidentList.map((i) => ({ id: i.id, status: i.status })) }),
      framework: "ISO27001",
      controlId: "A.16.1.4",
      source: "pagerduty/incidents",
      status: "unknown",
      data: {
        incidentCount: incidentList.length,
        resolved: incidentList.filter((i) => i.status === "resolved").length,
      },
      metadata: {},
    });

    return artifacts;
  }
}
