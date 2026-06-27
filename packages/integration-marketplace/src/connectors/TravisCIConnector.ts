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
    id: "travis-builds",
    name: "Build History",
    description: "Fetch Travis CI build configurations and results",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "travis-env",
    name: "Environment Variables",
    description: "Fetch encrypted environment variable configurations",
    evidenceCategories: ["data_protection", "access_control"],
  },
  {
    id: "travis-repos",
    name: "Repository Settings",
    description: "Fetch enabled repositories and branch settings",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "travis-cron",
    name: "Cron Jobs",
    description: "Fetch scheduled build configurations",
    evidenceCategories: ["change_management"],
  },
];

export class TravisCIConnector implements IntegrationConnector {
  readonly id = "travis-ci";
  readonly name = "Travis CI";
  readonly category = "ci_cd" as const;
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
    const base = config.baseUrl || "https://api.travis-ci.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Token ${config.apiToken}`,
        "Travis-API-Version": "3",
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Travis CI API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/repos");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const repo = config.extra?.repo || "default/repo";

    const builds = await this.fetchApi(config, `/repo/${repo.replace("/", "%2F")}/builds?limit=10`).catch(
      () => ({ builds: [] })
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "travis-builds",
      timestamp: now,
      hash: hashEvidence(builds),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `travis-ci.com/${repo}`,
      status: "partial",
      data: { recentBuilds: (builds.builds as unknown[])?.length || 0 },
      metadata: { repo },
    });

    const settings = await this.fetchApi(config, `/repo/${repo.replace("/", "%2F")}/settings`).catch(
      () => ({})
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "travis-repos",
      timestamp: now,
      hash: hashEvidence(settings as Record<string, unknown>),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: `travis-ci.com/${repo}/settings`,
      status: "partial",
      data: settings as Record<string, unknown>,
      metadata: { repo },
    });

    return artifacts;
  }
}
