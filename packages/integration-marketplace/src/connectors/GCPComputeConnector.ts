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
    id: "gcpcompute-instances",
    name: "Compute Instances",
    description: "Fetch GCP Compute Engine instance configurations and metadata",
    evidenceCategories: ["cloud_configuration", "infrastructure"],
  },
  {
    id: "gcpcompute-firewall",
    name: "Firewall Rules",
    description: "Fetch VPC firewall rules and network access controls",
    evidenceCategories: ["network_security", "access_control"],
  },
  {
    id: "gcpcompute-osconfig",
    name: "OS Patch Management",
    description: "Fetch OS patch policies and compliance status for compute instances",
    evidenceCategories: ["vulnerability_management", "configuration"],
  },
];

export class GCPComputeConnector implements IntegrationConnector {
  readonly id = "gcp-compute";
  readonly name = "GCP Compute Engine";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const project = config.extra?.project || "default";
    const base = config.baseUrl || `https://compute.googleapis.com/compute/v1/projects/${project}`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`GCP Compute API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/aggregated/instances?maxResults=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const instances = await this.fetchApi(config, "/aggregated/instances").catch(() => ({ items: {} }));
    const items = instances.items as Record<string, unknown> || {};
    const instanceCount = Object.keys(items).length;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcpcompute-instances",
      timestamp: now,
      hash: hashEvidence({ instanceCount }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "gcp-compute/instances",
      status: "unknown",
      data: { instanceCount },
      metadata: {},
    });

    const firewalls = await this.fetchApi(config, "/global/firewalls").catch(() => ({ items: [] }));
    const fwList = (firewalls.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcpcompute-firewall",
      timestamp: now,
      hash: hashEvidence({ ruleCount: fwList.length }),
      framework: "ISO27001",
      controlId: "A.13.1.1",
      source: "gcp-compute/firewalls",
      status: "unknown",
      data: { firewallRuleCount: fwList.length },
      metadata: {},
    });

    return artifacts;
  }
}
