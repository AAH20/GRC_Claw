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
    id: "palantir-foundry",
    name: "Foundry Datasets",
    description: "Fetch dataset access controls and lineage metadata",
    evidenceCategories: ["data_protection", "access_control"],
  },
  {
    id: "palantir-ontologies",
    name: "Ontology Management",
    description: "Fetch ontology object types and action permissions",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "palantir-pipelines",
    name: "Data Pipelines",
    description: "Fetch pipeline schedules and transformation configs",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "palantir-audit",
    name: "Audit Events",
    description: "Fetch user activity and data access audit logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class PalantirConnector implements IntegrationConnector {
  readonly id = "palantir";
  readonly name = "Palantir Foundry";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://foundry.palantir.com";
    const resp = await fetch(`${base}/api${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Palantir API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/datasets");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const project = config.extra?.project || "default";

    const datasets = await this.fetchApi(
      config,
      `/datasets?project=${project}`
    ).catch(() => ({ results: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "palantir-foundry",
      timestamp: now,
      hash: hashEvidence(datasets),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `palantir/${project}/datasets`,
      status: (datasets.results as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { datasetCount: (datasets.results as unknown[])?.length || 0 },
      metadata: { project },
    });

    const pipelines = await this.fetchApi(
      config,
      `/pipelines?project=${project}`
    ).catch(() => ({ results: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "palantir-pipelines",
      timestamp: now,
      hash: hashEvidence(pipelines),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: `palantir/${project}/pipelines`,
      status: (pipelines.results as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { pipelineCount: (pipelines.results as unknown[])?.length || 0 },
      metadata: { project },
    });

    return artifacts;
  }
}
