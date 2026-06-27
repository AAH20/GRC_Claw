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
    id: "ringcentral-users",
    name: "User Management",
    description: "Fetch user accounts, roles, and extension assignments",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "ringcentral-policies",
    name: "Phone System Policies",
    description: "Fetch call handling, IVR, and routing policies",
    evidenceCategories: ["configuration", "access_control"],
  },
  {
    id: "ringcentral-recording",
    name: "Call Recording",
    description: "Fetch call recording settings and compliance configurations",
    evidenceCategories: ["data_protection", "compliance"],
  },
  {
    id: "ringcentral-audit",
    name: "Audit Logs",
    description: "Fetch admin and user activity audit logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class RingCentralConnector implements IntegrationConnector {
  readonly id = "ringcentral";
  readonly name = "RingCentral";
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
    const base = config.baseUrl || "https://platform.ringcentral.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`RingCentral API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/restapi/v1.0/account/~/extension");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const extensions = await this.fetchApi(
      config,
      "/restapi/v1.0/account/~/extension?type=Employee&status=Enabled&perPage=100"
    ).catch(() => ({ records: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "ringcentral-users",
      timestamp: now,
      hash: hashEvidence(extensions),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "ringcentral/extensions",
      status: (extensions.records as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { activeExtensions: (extensions.records as unknown[])?.length || 0 },
      metadata: {},
    });

    const recording = await this.fetchApi(
      config,
      "/restapi/v1.0/account/~/answering-rule"
    ).catch(() => ({ records: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "ringcentral-recording",
      timestamp: now,
      hash: hashEvidence(recording),
      framework: "HIPAA",
      controlId: "164.312",
      source: "ringcentral/answering-rules",
      status: (recording.records as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { answeringRules: (recording.records as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
