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
    id: "webex-meetings",
    name: "Meeting Policies",
    description: "Fetch Webex meeting security and lobby settings",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "webex-devices",
    name: "Device Management",
    description: "Fetch registered device compliance and firmware status",
    evidenceCategories: ["endpoint", "configuration"],
  },
  {
    id: "webex-users",
    name: "User Provisioning",
    description: "Fetch user accounts, roles, and license assignments",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "webex-audit",
    name: "Admin Audit",
    description: "Fetch admin activity and configuration change logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class WebexConnector implements IntegrationConnector {
  readonly id = "webex";
  readonly name = "Cisco Webex";
  readonly category = "communication" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://webexapis.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Webex API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/people/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const people = await this.fetchApi(config, "/people?max=100").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "webex-users",
      timestamp: now,
      hash: hashEvidence(people),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "webex/people",
      status: (people.items as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { userCount: (people.items as unknown[])?.length || 0 },
      metadata: {},
    });

    const devices = await this.fetchApi(config, "/devices").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "webex-devices",
      timestamp: now,
      hash: hashEvidence(devices),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "webex/devices",
      status: (devices.items as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { registeredDevices: (devices.items as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
