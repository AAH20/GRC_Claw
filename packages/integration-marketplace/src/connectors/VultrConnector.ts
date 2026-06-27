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
    id: "vultr-instances",
    name: "Cloud Instances",
    description: "Fetch Vultr compute instance configurations and status",
    evidenceCategories: ["cloud_configuration", "infrastructure"],
  },
  {
    id: "vultr-firewalls",
    name: "Firewall Groups",
    description: "Fetch firewall group rules and network access controls",
    evidenceCategories: ["network_security", "access_control"],
  },
  {
    id: "vultr-dns",
    name: "DNS Domains",
    description: "Fetch managed DNS domain configurations",
    evidenceCategories: ["configuration", "infrastructure"],
  },
];

export class VultrConnector implements IntegrationConnector {
  readonly id = "vultr";
  readonly name = "Vultr";
  readonly category = "cloud_provider" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.vultr.com/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Vultr API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/accounts");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const instances = await this.fetchApi(config, "/instances").catch(() => ({ instances: [] }));
    const instanceList = (instances.instances || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "vultr-instances",
      timestamp: now,
      hash: hashEvidence({ instanceCount: instanceList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "vultr/instances",
      status: "unknown",
      data: { instanceCount: instanceList.length },
      metadata: {},
    });

    return artifacts;
  }
}
