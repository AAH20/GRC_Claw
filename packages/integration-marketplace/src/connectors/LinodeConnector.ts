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
    id: "linode-linodes",
    name: "Linode Instances",
    description: "Fetch Linode instance configurations and status",
    evidenceCategories: ["cloud_configuration", "infrastructure"],
  },
  {
    id: "linode-firewalls",
    name: "Cloud Firewalls",
    description: "Fetch cloud firewall rules and network policies",
    evidenceCategories: ["network_security", "access_control"],
  },
  {
    id: "linode-volumes",
    name: "Block Storage",
    description: "Fetch block storage volume configurations and encryption status",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
];

export class LinodeConnector implements IntegrationConnector {
  readonly id = "linode";
  readonly name = "Linode (Akamai)";
  readonly category = "cloud_provider" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.linode.com/v4";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Linode API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/linode/instances?pageSize=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const linodes = await this.fetchApi(config, "/linode/instances?pageSize=100").catch(() => ({ data: [] }));
    const linodeList = (linodes.data || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "linode-linodes",
      timestamp: now,
      hash: hashEvidence({ instanceCount: linodeList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "linode/instances",
      status: "unknown",
      data: { instanceCount: linodeList.length },
      metadata: {},
    });

    return artifacts;
  }
}
