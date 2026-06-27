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
    id: "argocd-apps",
    name: "Application Definitions",
    description: "Fetch ArgoCD application sync status and health",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "argocd-repos",
    name: "Repository Credentials",
    description: "Fetch configured repository connections and RBAC",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "argocd-projects",
    name: "App Projects",
    description: "Fetch project restrictions and source/repo allowlists",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
 id: "argocd-audit",
    name: "Audit Logs",
    description: "Fetch ArgoCD event and audit logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class ArgoCDConnector implements IntegrationConnector {
  readonly id = "argocd";
  readonly name = "Argo CD";
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
    const base = config.baseUrl || "https://argocd.example.com";
    const resp = await fetch(`${base}/api/v1${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`ArgoCD API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/account");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const apps = await this.fetchApi(config, "/applications").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "argocd-apps",
      timestamp: now,
      hash: hashEvidence(apps),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "argocd/applications",
      status: (apps.items as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { applicationCount: (apps.items as unknown[])?.length || 0 },
      metadata: {},
    });

    const projects = await this.fetchApi(config, "/projects").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "argocd-projects",
      timestamp: now,
      hash: hashEvidence(projects),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "argocd/projects",
      status: (projects.items as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { projectCount: (projects.items as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
