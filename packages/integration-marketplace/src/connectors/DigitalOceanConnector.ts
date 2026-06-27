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
    id: "do-droplets",
    name: "Droplets",
    description: "Fetch DigitalOcean droplet configurations and status",
    evidenceCategories: ["cloud_configuration", "infrastructure"],
  },
  {
    id: "do-firewalls",
    name: "Cloud Firewalls",
    description: "Fetch cloud firewall rules and inbound/outbound policies",
    evidenceCategories: ["network_security", "access_control"],
  },
  {
    id: "do-vpc",
    name: "VPC Networks",
    description: "Fetch VPC configurations and IP range allocations",
    evidenceCategories: ["network_security", "cloud_configuration"],
  },
];

export class DigitalOceanConnector implements IntegrationConnector {
  readonly id = "digitalocean";
  readonly name = "DigitalOcean";
  readonly category = "cloud_provider" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.digitalocean.com/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`DigitalOcean API ${resp.status}: ${resp.statusText}`);
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

    const droplets = await this.fetchApi(config, "/droplets?per_page=100").catch(() => ({ droplets: [] }));
    const dropletList = (droplets.droplets || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "do-droplets",
      timestamp: now,
      hash: hashEvidence({ dropletCount: dropletList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "digitalocean/droplets",
      status: "unknown",
      data: { dropletCount: dropletList.length },
      metadata: {},
    });

    const firewalls = await this.fetchApi(config, "/firewalls").catch(() => ({ firewalls: [] }));
    const fwList = (firewalls.firewalls || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "do-firewalls",
      timestamp: now,
      hash: hashEvidence({ firewallCount: fwList.length }),
      framework: "ISO27001",
      controlId: "A.13.1.1",
      source: "digitalocean/firewalls",
      status: fwList.length > 0 ? "compliant" : "non_compliant",
      data: { firewallCount: fwList.length },
      metadata: {},
    });

    return artifacts;
  }
}
