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
    id: "launchdarkly-flags",
    name: "Feature Flags",
    description: "Fetch LaunchDarkly feature flag configurations and targeting rules",
    evidenceCategories: ["configuration", "change_management"],
  },
  {
    id: "launchdarkly-audit",
    name: "Audit Log",
    description: "Fetch LaunchDarkly audit log events for flag changes and approvals",
    evidenceCategories: ["audit", "change_management"],
  },
  {
    id: "launchdarkly-access",
    name: "Access Controls",
    description: "Fetch LaunchDarkly role assignments and API key management",
    evidenceCategories: ["access_control", "secret_management"],
  },
];

export class LaunchDarklyConnector implements IntegrationConnector {
  readonly id = "launchdarkly";
  readonly name = "LaunchDarkly";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://app.launchdarkly.com/api/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`LaunchDarkly API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/projects");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const project = config.extra?.project || "default";

    const flags = await this.fetchApi(
      config,
      `/projects/${project}/flags?limit=100`
    ).catch(() => ({ items: [] }));
    const flagList = (flags.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "launchdarkly-flags",
      timestamp: now,
      hash: hashEvidence({ flagCount: flagList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "launchdarkly/flags",
      status: "unknown",
      data: { flagCount: flagList.length },
      metadata: { project },
    });

    const auditLog = await this.fetchApi(
      config,
      `/auditlog?limit=100`
    ).catch(() => ({ items: [] }));
    const auditList = (auditLog.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "launchdarkly-audit",
      timestamp: now,
      hash: hashEvidence({ auditCount: auditList.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "launchdarkly/auditlog",
      status: "unknown",
      data: { recentAuditEvents: auditList.length },
      metadata: {},
    });

    return artifacts;
  }
}
