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
    id: "zapier-zaps",
    name: "Zap Workflows",
    description: "Fetch Zapier zap configurations, task history, and error rates",
    evidenceCategories: ["automation", "configuration"],
  },
  {
    id: "zapier-connections",
    name: "App Connections",
    description: "Fetch connected app credentials and OAuth token status",
    evidenceCategories: ["access_control", "secret_management"],
  },
  {
    id: "zapier-audit",
    name: "Task Audit Log",
    description: "Fetch Zapier task execution history and failure audit events",
    evidenceCategories: ["monitoring", "audit"],
  },
];

export class ZapierConnector implements IntegrationConnector {
  readonly id = "zapier";
  readonly name = "Zapier";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.zapier.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Zapier API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/zaps?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const zaps = await this.fetchApi(config, "/zaps?limit=100").catch(() => ({ items: [] }));
    const zapList = (zaps.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "zapier-zaps",
      timestamp: now,
      hash: hashEvidence({ zapCount: zapList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "zapier/zaps",
      status: "unknown",
      data: { zapCount: zapList.length },
      metadata: {},
    });

    return artifacts;
  }
}
