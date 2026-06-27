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
    id: "teamcity-builds",
    name: "Build Configurations",
    description: "Fetch TeamCity build configurations and VCS root settings",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "teamcity-agents",
    name: "Build Agents",
    description: "Fetch TeamCity build agent status and pool assignments",
    evidenceCategories: ["infrastructure", "monitoring"],
  },
  {
    id: "teamcity-security",
    name: "Build Security",
    description: "Fetch TeamCity build trigger rules and access tokens",
    evidenceCategories: ["access_control", "secret_management"],
  },
];

export class TeamCityConnector implements IntegrationConnector {
  readonly id = "teamcity";
  readonly name = "JetBrains TeamCity";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://teamcity.example.com/app/rest";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`TeamCity API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/buildTypes?count=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const builds = await this.fetchApi(config, "/buildTypes?count=100").catch(() => ({ buildType: [] }));
    const buildList = (builds.buildType || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "teamcity-builds",
      timestamp: now,
      hash: hashEvidence({ buildConfigCount: buildList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "teamcity/buildTypes",
      status: "unknown",
      data: { buildConfigCount: buildList.length },
      metadata: {},
    });

    return artifacts;
  }
}
