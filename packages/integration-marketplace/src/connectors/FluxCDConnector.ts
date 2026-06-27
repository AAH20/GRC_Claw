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
    id: "flux-reconcile",
    name: "Reconciliation Status",
    description: "Fetch FluxCD source and kustomization reconciliation status",
    evidenceCategories: ["change_management", "monitoring"],
  },
  {
    id: "flux-repositories",
    name: "Git Repositories",
    description: "Fetch GitRepository source configurations and drift detection",
    evidenceCategories: ["access_control", "change_management"],
  },
  {
    id: "flux-policies",
    name: "Image Policies",
    description: "Fetch image update automation and policies",
    evidenceCategories: ["change_management", "data_protection"],
  },
  {
    id: "flux-alerts",
    name: "Alert Provider",
    description: "Fetch alert configurations and notification status",
    evidenceCategories: ["monitoring"],
  },
];

export class FluxCDConnector implements IntegrationConnector {
  readonly id = "fluxcd";
  readonly name = "FluxCD";
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
    const base = config.baseUrl || "https://flux.example.com";
    const resp = await fetch(`${base}/apis${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`FluxCD API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/kustomize.toolkit.fluxcd.io/v1/namespaces");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const ns = config.extra?.namespace || "flux-system";

    const kustomizations = await this.fetchApi(
      config,
      `/kustomize.toolkit.fluxcd.io/v1/namespaces/${ns}/kustomizations`
    ).catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "flux-reconcile",
      timestamp: now,
      hash: hashEvidence(kustomizations),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `fluxcd/${ns}/kustomizations`,
      status: (kustomizations.items as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { kustomizationCount: (kustomizations.items as unknown[])?.length || 0 },
      metadata: { namespace: ns },
    });

    const gitrepos = await this.fetchApi(
      config,
      `/source.toolkit.fluxcd.io/v1/namespaces/${ns}/gitrepositories`
    ).catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "flux-repositories",
      timestamp: now,
      hash: hashEvidence(gitrepos),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: `fluxcd/${ns}/gitrepositories`,
      status: (gitrepos.items as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { gitRepositoryCount: (gitrepos.items as unknown[])?.length || 0 },
      metadata: { namespace: ns },
    });

    return artifacts;
  }
}
