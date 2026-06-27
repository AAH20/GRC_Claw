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
    id: "slack-workspace",
    name: "Workspace Settings",
    description: "Fetch Slack workspace security and compliance settings",
    evidenceCategories: ["configuration", "access_control"],
  },
  {
    id: "slack-apps",
    name: "App Installations",
    description: "Fetch installed apps and their permissions",
    evidenceCategories: ["access_control", "third_party_management"],
  },
  {
    id: "slack-channels",
    name: "Channel Access",
    description: "Fetch channel privacy and access controls",
    evidenceCategories: ["access_control", "data_protection"],
  },
];

export class SlackConnector implements IntegrationConnector {
  readonly id = "slack";
  readonly name = "Slack";
  readonly category = "communication" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://slack.com/api";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `Bearer ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`Slack API ${resp.status}: ${resp.statusText}`);
    const data = (await resp.json()) as Record<string, unknown>;
    if (data.ok === false) throw new Error(`Slack error: ${data.error}`);
    return data;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/auth.test");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const team = await this.fetchApi(config, "/team.info");
    const teamData = (team.team || {}) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "slack-workspace",
      timestamp: now,
      hash: hashEvidence(team),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "slack/team.info",
      status: "compliant",
      data: {
        teamId: teamData.id,
        teamName: teamData.name,
        domain: teamData.domain,
        emailDomain: teamData.email_domain,
      },
      metadata: { workspace: String(teamData.domain || "") },
    });

    const apps = await this.fetchApi(config, "/apps.permissions.list").catch(() => ({
      scopes: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "slack-apps",
      timestamp: now,
      hash: hashEvidence(apps),
      framework: "ISO27001",
      controlId: "A.14.2.5",
      source: "slack/apps.permissions.list",
      status: "unknown",
      data: { appScopes: apps.scopes },
      metadata: { workspace: String(teamData.domain || "") },
    });

    const channels = await this.fetchApi(config, "/conversations.list?types=public_channel,private_channel&limit=200").catch(() => ({
      channels: [],
    }));
    const channelList = (channels.channels || []) as Record<string, unknown>[];
    const privateChannels = channelList.filter((c) => c.is_private === true);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "slack-channels",
      timestamp: now,
      hash: hashEvidence({ total: channelList.length, private: privateChannels.length }),
      framework: "SOC2",
      controlId: "CC6.4",
      source: "slack/conversations.list",
      status: "unknown",
      data: { totalChannels: channelList.length, privateChannels: privateChannels.length },
      metadata: { workspace: String(teamData.domain || "") },
    });

    return artifacts;
  }
}
