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
    id: "spinnaker-pipelines",
    name: "Deployment Pipelines",
    description: "Fetch Spinnaker pipeline configurations and execution history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "spinnaker-applications",
    name: "Applications",
    description: "Fetch Spinnaker application definitions and cluster configurations",
    evidenceCategories: ["cloud_configuration", "change_management"],
  },
  {
    id: "spinnaker-rollback",
    name: "Rollback Policies",
    description: "Fetch automatic rollback configurations and canary analysis",
    evidenceCategories: ["disaster_recovery", "configuration"],
  },
];

export class SpinnakerConnector implements IntegrationConnector {
  readonly id = "spinnaker";
  readonly name = "Spinnaker";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://spinnaker.example.com";
    const resp = await fetch(`${base}/gate${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Spinnaker API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/applications?expand=false");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const apps = await this.fetchApi(config, "/applications?expand=false").catch(() => []);
    const appList = Array.isArray(apps) ? apps : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "spinnaker-applications",
      timestamp: now,
      hash: hashEvidence({ appCount: appList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "spinnaker/applications",
      status: "unknown",
      data: { applicationCount: appList.length },
      metadata: {},
    });

    return artifacts;
  }
}
