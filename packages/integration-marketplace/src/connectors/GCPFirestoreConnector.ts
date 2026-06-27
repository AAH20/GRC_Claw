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
    id: "gcpfirestore-collections",
    name: "Firestore Collections",
    description: "Fetch Firestore collection configurations and document counts",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "gcpfirestore-security",
    name: "Security Rules",
    description: "Fetch Firestore security rules and access control configurations",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "gcpfirestore-backups",
    name: "Backup Status",
    description: "Fetch Firestore backup schedules and point-in-time recovery settings",
    evidenceCategories: ["data_protection", "disaster_recovery"],
  },
];

export class GCPFirestoreConnector implements IntegrationConnector {
  readonly id = "gcp-firestore";
  readonly name = "GCP Firestore";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const project = config.extra?.project || "default";
    const base = config.baseUrl || `https://firestore.googleapis.com/v1/projects/${project}`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`GCP Firestore API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/databases/(default)/documents?pageSize=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const docs = await this.fetchApi(config, "/databases/(default)/documents?pageSize=100").catch(() => ({ documents: [] }));
    const docList = (docs.documents || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcpfirestore-collections",
      timestamp: now,
      hash: hashEvidence({ documentCount: docList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "gcp-firestore/documents",
      status: "unknown",
      data: { documentCount: docList.length },
      metadata: {},
    });

    return artifacts;
  }
}
