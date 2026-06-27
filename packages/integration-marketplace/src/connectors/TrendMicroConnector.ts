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
    id: "trendmicro-endpoints",
    name: "Endpoint Protection",
    description: "Fetch Trend Micro endpoint security agent status and policy compliance",
    evidenceCategories: ["endpoint_security", "posture_assessment"],
  },
  {
    id: "trendmicro-detections",
    name: "Threat Detections",
    description: "Fetch threat detection events and malware quarantine events",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "trendmicro-network",
    name: "Network Inspection",
    description: "Fetch network inspection rules and IPS/IDS event summaries",
    evidenceCategories: ["network_security", "configuration"],
  },
];

export class TrendMicroConnector implements IntegrationConnector {
  readonly id = "trendmicro";
  readonly name = "Trend Micro";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://app.deepsecurity.trendmicro.com/api";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `ApiKey ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Trend Micro API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/computers?expand=none&maxComputerCount=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const computers = await this.fetchApi(
      config,
      "/computers?expand=none&maxComputerCount=100"
    ).catch(() => ({ computers: [] }));
    const computerList = (computers.computers || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "trendmicro-endpoints",
      timestamp: now,
      hash: hashEvidence({ computerCount: computerList.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "trendmicro/computers",
      status: computerList.length > 0 ? "compliant" : "unknown",
      data: { endpointCount: computerList.length },
      metadata: {},
    });

    const events = await this.fetchApi(config, "/events?maxCount=10").catch(() => ({ events: [] }));
    const eventList = (events.events || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "trendmicro-detections",
      timestamp: now,
      hash: hashEvidence({ eventCount: eventList.length }),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "trendmicro/events",
      status: eventList.length === 0 ? "compliant" : "non_compliant",
      data: { recentEvents: eventList.length },
      metadata: {},
    });

    return artifacts;
  }
}
