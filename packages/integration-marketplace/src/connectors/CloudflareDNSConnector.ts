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
    id: "cloudflare-dns",
    name: "DNS Configurations",
    description: "Fetch Cloudflare DNS zone configurations and record counts",
    evidenceCategories: ["network_security", "configuration"],
  },
  {
    id: "cloudflare-ssl",
    name: "SSL/TLS Settings",
    description: "Fetch Cloudflare SSL/TLS mode, HSTS, and certificate status",
    evidenceCategories: ["encryption", "configuration"],
  },
  {
    id: "cloudflare-analytics",
    name: "Traffic Analytics",
    description: "Fetch Cloudflare traffic statistics and threat detection metrics",
    evidenceCategories: ["monitoring", "network_security"],
  },
];

export class CloudflareDNSConnector implements IntegrationConnector {
  readonly id = "cloudflare-dns";
  readonly name = "Cloudflare DNS";
  readonly category = "infrastructure" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.cloudflare.com/client/v4";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Cloudflare API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/user/tokens/verify");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const zoneId = config.extra?.zoneId || "default";

    const zone = await this.fetchApi(config, `/zones/${zoneId}`).catch(() => ({ result: {} }));
    const result = zone.result as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cloudflare-dns",
      timestamp: now,
      hash: hashEvidence(result),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "cloudflare-dns/zone",
      status: "unknown",
      data: { zoneName: result.name },
      metadata: { zoneId },
    });

    return artifacts;
  }
}
