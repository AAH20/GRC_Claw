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
    id: "splunk-indexes",
    name: "Index Overview",
    description: "Fetch Splunk index configurations and data volumes",
    evidenceCategories: ["log_management", "configuration"],
  },
  {
    id: "splunk-saved-searches",
    name: "Saved Searches & Alerts",
    description: "Fetch saved searches, alerts, and correlation rules",
    evidenceCategories: ["monitoring", "alerting"],
  },
  {
    id: "splunk-sourcetypes",
    name: "Source Types",
    description: "Fetch ingested source types and event volumes",
    evidenceCategories: ["log_management", "data_collection"],
  },
  {
    id: "splunk-users",
    name: "User Accounts",
    description: "Fetch Splunk user accounts and role assignments",
    evidenceCategories: ["access_control", "identity_management"],
  },
];

export class SplunkConnector implements IntegrationConnector {
  readonly id = "splunk";
  readonly name = "Splunk";
  readonly category = "siem" as const;
  readonly authType = "basic_auth" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || `https://${config.extra?.host || "localhost"}:8089`;
    const auth = Buffer.from(`${config.clientId || ""}:${config.clientSecret || ""}`).toString("base64");
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Accept: "application/json",
        Authorization: `Basic ${auth}`,
      },
    });
    if (!resp.ok) throw new Error(`Splunk API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/services/server/info?output_mode=json");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const indexes = await this.fetchApi(
      config,
      "/services/data/indexes?output_mode=json&count=0"
    ).catch(() => ({ entry: [] }));
    const indexList = (indexes.entry || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "splunk-indexes",
      timestamp: now,
      hash: hashEvidence({ indexCount: indexList.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "splunk/indexes",
      status: indexList.length > 0 ? "compliant" : "non_compliant",
      data: { indexCount: indexList.length },
      metadata: { host: config.extra?.host || "" },
    });

    const searches = await this.fetchApi(
      config,
      "/services/saved/searches?output_mode=json&count=0"
    ).catch(() => ({ entry: [] }));
    const searchList = (searches.entry || []) as Record<string, unknown>[];
    const alerts = searchList.filter((s) => {
      const cont = (s.content || {}) as Record<string, unknown>;
      return cont.alert === 1 || cont.alert === true;
    });
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "splunk-saved-searches",
      timestamp: now,
      hash: hashEvidence({ total: searchList.length, alerts: alerts.length }),
      framework: "ISO27001",
      controlId: "A.12.4.1",
      source: "splunk/saved/searches",
      status: "unknown",
      data: { searchCount: searchList.length, alertCount: alerts.length },
      metadata: { host: config.extra?.host || "" },
    });

    const sourcetypes = await this.fetchApi(
      config,
      "/services/data/indexes-extended?output_mode=json&count=0"
    ).catch(() => ({ entry: [] }));
    const stList = (sourcetypes.entry || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "splunk-sourcetypes",
      timestamp: now,
      hash: hashEvidence({ sourcetypeCount: stList.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "splunk/indexes-extended",
      status: "unknown",
      data: { sourcetypeCount: stList.length },
      metadata: { host: config.extra?.host || "" },
    });

    const users = await this.fetchApi(
      config,
      "/services/admin/users?output_mode=json&count=0"
    ).catch(() => ({ entry: [] }));
    const userList = (users.entry || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "splunk-users",
      timestamp: now,
      hash: hashEvidence({ userCount: userList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "splunk/admin/users",
      status: "unknown",
      data: { userCount: userList.length },
      metadata: { host: config.extra?.host || "" },
    });

    return artifacts;
  }
}
