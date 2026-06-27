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
    id: "featureflag-flags",
    name: "Feature Flags",
    description: "Fetch feature flag definitions, targeting rules, and percentage rollouts",
    evidenceCategories: ["configuration", "change_management"],
  },
  {
    id: "featureflag-audit",
    name: "Change Audit Trail",
    description: "Fetch flag change history and approval workflows",
    evidenceCategories: ["audit", "change_management"],
  },
  {
    id: "featureflag-environments",
    name: "Environment Segmentation",
    description: "Fetch environment-specific flag configurations and overrides",
    evidenceCategories: ["access_control", "configuration"],
  },
];

export class FeatureFlagConnector implements IntegrationConnector {
  readonly id = "featureflag";
  readonly name = "Feature Flag Service";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.featureflags.example.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Feature Flag API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/flags?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const flags = await this.fetchApi(config, "/flags?limit=100").catch(() => ({ items: [] }));
    const flagList = (flags.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "featureflag-flags",
      timestamp: now,
      hash: hashEvidence({ flagCount: flagList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "featureflag/flags",
      status: "unknown",
      data: { flagCount: flagList.length },
      metadata: {},
    });

    return artifacts;
  }
}
