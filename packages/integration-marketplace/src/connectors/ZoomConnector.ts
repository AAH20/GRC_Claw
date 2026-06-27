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
    id: "zoom-meetings",
    name: "Meeting Security",
    description: "Fetch Zoom meeting security settings and policies",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "zoom-users",
    name: "User Management",
    description: "Fetch user roles, SSO configurations, and MFA status",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "zoom-recording",
    name: "Recording Security",
    description: "Fetch cloud recording retention and access controls",
    evidenceCategories: ["data_protection", "configuration"],
  },
  {
    id: "zoom-audit",
    name: "Audit Logs",
    description: "Fetch admin activity and user session logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class ZoomConnector implements IntegrationConnector {
  readonly id = "zoom";
  readonly name = "Zoom";
  readonly category = "communication" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "GDPR",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.zoom.us/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Zoom API ${resp.status}: ${resp.statusText}`);
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

    const users = await this.fetchApi(config, "/users?status=active&page_size=100").catch(() => ({
      users: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "zoom-users",
      timestamp: now,
      hash: hashEvidence(users),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "zoom/users",
      status: (users.users as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { activeUsers: (users.users as unknown[])?.length || 0 },
      metadata: {},
    });

    const settings = await this.fetchApi(config, "/users/me/settings").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "zoom-meetings",
      timestamp: now,
      hash: hashEvidence(settings),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "zoom/settings",
      status: "partial",
      data: settings as Record<string, unknown>,
      metadata: {},
    });

    return artifacts;
  }
}
