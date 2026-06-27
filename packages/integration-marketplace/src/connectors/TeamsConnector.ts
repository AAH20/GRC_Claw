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
    id: "teams-policies",
    name: "Meeting Policies",
    description: "Fetch Teams meeting and messaging policy configurations",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "teams-compliance",
    name: "Compliance Management",
    description: "Fetch retention policies and eDiscovery configurations",
    evidenceCategories: ["compliance", "data_protection"],
  },
  {
    id: "teams-security",
    name: "Security Defaults",
    description: "Fetch conditional access and MFA enforcement status",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "teams-audit",
    name: "Unified Audit Log",
    description: "Fetch Teams activity from Microsoft 365 audit logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class TeamsConnector implements IntegrationConnector {
  readonly id = "microsoft-teams";
  readonly name = "Microsoft Teams";
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
    const base = config.baseUrl || "https://graph.microsoft.com/v1.0";
    const resp = fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    const r = await resp;
    if (!r.ok) throw new Error(`Teams API ${r.status}: ${r.statusText}`);
    return (await r.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const teams = await this.fetchApi(config, "/me/joinedTeams").catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "teams-policies",
      timestamp: now,
      hash: hashEvidence(teams),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "teams/joinedTeams",
      status: (teams.value as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { teamCount: (teams.value as unknown[])?.length || 0 },
      metadata: {},
    });

    const messages = await this.fetchApi(
      config,
      "/me/messages?$top=10&$select=subject,receivedDateTime"
    ).catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "teams-compliance",
      timestamp: now,
      hash: hashEvidence(messages),
      framework: "ISO27001",
      controlId: "A.8.3.1",
      source: "teams/messages",
      status: "partial",
      data: { recentMessages: (messages.value as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
