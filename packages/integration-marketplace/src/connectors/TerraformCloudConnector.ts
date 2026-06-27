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
    id: "tfc-workspaces",
    name: "Workspace Configs",
    description: "Fetch Terraform Cloud workspace configurations and variables",
    evidenceCategories: ["iac", "configuration"],
  },
  {
    id: "tfc-state",
    name: "State Files",
    description: "Fetch state file metadata and resource counts",
    evidenceCategories: ["iac", "change_management"],
  },
  {
    id: "tfc-drift",
    name: "Drift Detection",
    description: "Fetch drift detection results and policy violations",
    evidenceCategories: ["iac", "compliance"],
  },
];

export class TerraformCloudConnector implements IntegrationConnector {
  readonly id = "terraform-cloud";
  readonly name = "Terraform Cloud";
  readonly category = "iac" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://app.terraform.io/api/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/vnd.api+json",
      },
    });
    if (!resp.ok) throw new Error(`Terraform Cloud API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/organizations?filter[name]=default");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const org = config.extra?.org || "default";

    const workspaces = await this.fetchApi(
      config,
      `/organizations/${org}/workspaces`
    ).catch(() => ({ data: [] }));
    const wsList = Array.isArray(workspaces.data) ? workspaces.data : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tfc-workspaces",
      timestamp: now,
      hash: hashEvidence({ workspaceCount: wsList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `terraform-cloud/organizations/${org}/workspaces`,
      status: "unknown",
      data: { workspaceCount: wsList.length },
      metadata: { org },
    });

    const wsId = config.extra?.workspaceId || wsList[0]?.id || "";
    const state = wsId
      ? await this.fetchApi(config, `/workspaces/${wsId}/current-state-version`)
          .catch(() => ({ data: null }))
      : { data: null };
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tfc-state",
      timestamp: now,
      hash: hashEvidence(state),
      framework: "ISO27001",
      controlId: "A.12.3.1",
      source: `terraform-cloud/workspaces/${wsId}/state`,
      status: state.data ? "compliant" : "non_compliant",
      data: { stateVersion: state.data },
      metadata: { org, workspaceId: wsId },
    });

    const runs = wsId
      ? await this.fetchApi(config, `/workspaces/${wsId}/runs?filter[status]=planned,errored&filter[kinds][]=drift`).catch(() => ({ data: [] }))
      : { data: [] };
    const runList = Array.isArray(runs.data) ? runs.data : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tfc-drift",
      timestamp: now,
      hash: hashEvidence({ driftRuns: runList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `terraform-cloud/workspaces/${wsId}/drift`,
      status: runList.length === 0 ? "compliant" : "non_compliant",
      data: { driftRuns: runList.length },
      metadata: { org, workspaceId: wsId },
    });

    return artifacts;
  }
}
