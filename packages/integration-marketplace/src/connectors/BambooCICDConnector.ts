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
    id: "bamboo-plans",
    name: "Build Plans",
    description: "Fetch Bamboo build plan configurations and execution history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "bamboo-deployments",
    name: "Deployment Projects",
    description: "Fetch Bamboo deployment project configurations and release history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "bamboo-permissions",
    name: "Plan Permissions",
    description: "Fetch Bamboo build plan access controls and agent authorizations",
    evidenceCategories: ["access_control", "configuration"],
  },
];

export class BambooCICDConnector implements IntegrationConnector {
  readonly id = "bamboo-cicd";
  readonly name = "Atlassian Bamboo";
  readonly category = "ci_cd" as const;
  readonly authType = "basic_auth" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://bamboo.example.com/rest/api/latest";
    const auth = Buffer.from(`${config.clientId}:${config.clientSecret}`).toString("base64");
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Basic ${auth}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Bamboo API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/plan.json?maxResults=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const plans = await this.fetchApi(config, "/plan.json?maxResults=100").catch(() => ({ plans: { plan: [] as unknown[] } }));
    const planData = plans.plans as Record<string, unknown> | undefined;
    const planList = ((planData?.plan || []) as Record<string, unknown>[]);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "bamboo-plans",
      timestamp: now,
      hash: hashEvidence({ planCount: planList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "bamboo/plans",
      status: "unknown",
      data: { planCount: planList.length },
      metadata: {},
    });

    return artifacts;
  }
}
