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
    id: "ifttt-applets",
    name: "Applet Configurations",
    description: "Fetch IFTTT applet configurations and execution history",
    evidenceCategories: ["automation", "configuration"],
  },
  {
    id: "ifttt-connections",
    name: "Service Connections",
    description: "Fetch connected service authorizations and API key usage",
    evidenceCategories: ["access_control", "secret_management"],
  },
  {
    id: "ifttt-logs",
    name: "Execution Logs",
    description: "Fetch IFTTT applet run history and error/failure records",
    evidenceCategories: ["monitoring", "audit"],
  },
];

export class IFTTTConnector implements IntegrationConnector {
  readonly id = "ifttt";
  readonly name = "IFTTT";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.ifttt.com/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`IFTTT API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/applets?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const applets = await this.fetchApi(config, "/applets?limit=100").catch(() => ({ data: [] }));
    const appletList = (applets.data || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "ifttt-applets",
      timestamp: now,
      hash: hashEvidence({ appletCount: appletList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "ifttt/applets",
      status: "unknown",
      data: { appletCount: appletList.length },
      metadata: {},
    });

    return artifacts;
  }
}
