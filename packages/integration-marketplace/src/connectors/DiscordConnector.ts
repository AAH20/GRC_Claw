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
    id: "discord-servers",
    name: "Server Settings",
    description: "Fetch Discord server verification and security settings",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "discord-roles",
    name: "Role Management",
    description: "Fetch server roles and permission configurations",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "discord-audit",
    name: "Audit Logs",
    description: "Fetch Discord server audit log entries",
    evidenceCategories: ["monitoring", "access_control"],
  },
  {
    id: "discord-integrations",
    name: "Bot & Webhook Security",
    description: "Fetch bot permissions and webhook configurations",
    evidenceCategories: ["access_control", "data_protection"],
  },
];

export class DiscordConnector implements IntegrationConnector {
  readonly id = "discord";
  readonly name = "Discord";
  readonly category = "communication" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://discord.com/api/v10";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bot ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Discord API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/users/@me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const guildId = config.extra?.guildId || "";

    const guild = await this.fetchApi(config, `/guilds/${guildId}?with_counts=true`).catch(
      () => ({})
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "discord-servers",
      timestamp: now,
      hash: hashEvidence(guild as Record<string, unknown>),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `discord/${guildId}`,
      status: (guild as Record<string, unknown>).id ? "compliant" : "unknown",
      data: {
        name: (guild as Record<string, unknown>).name,
        verificationLevel: (guild as Record<string, unknown>).verification_level,
        mfaLevel: (guild as Record<string, unknown>).mfa_level,
      },
      metadata: { guildId },
    });

    const roles = await this.fetchApi(config, `/guilds/${guildId}/roles`).catch(() => []);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "discord-roles",
      timestamp: now,
      hash: hashEvidence(Array.isArray(roles) ? { count: roles.length } : roles as Record<string, unknown>),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: `discord/${guildId}/roles`,
      status: Array.isArray(roles) && roles.length > 0 ? "compliant" : "non_compliant",
      data: { roleCount: Array.isArray(roles) ? roles.length : 0 },
      metadata: { guildId },
    });

    return artifacts;
  }
}
