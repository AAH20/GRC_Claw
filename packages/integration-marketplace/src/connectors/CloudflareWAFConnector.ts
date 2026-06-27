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
    id: "cloudflare-waf-rules",
    name: "WAF Rules",
    description: "Fetch managed and custom WAF rule configurations",
    evidenceCategories: ["vulnerability_management", "configuration"],
  },
  {
    id: "cloudflare-firewall",
    name: "Firewall Rules",
    description: "Fetch firewall rules and IP access lists",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "cloudflare-ddos",
    name: "DDoS Protection",
    description: "Fetch DDoS mitigation settings and attack analytics",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "cloudflare-ssl",
    name: "SSL/TLS Configuration",
    description: "Fetch SSL/TLS mode and certificate status",
    evidenceCategories: ["data_protection", "configuration"],
  },
];

export class CloudflareWAFConnector implements IntegrationConnector {
  readonly id = "cloudflare-waf";
  readonly name = "Cloudflare WAF";
  readonly category = "cloud_provider" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.cloudflare.com";
    const zoneId = config.extra?.zoneId || "default";
    const resp = await fetch(`${base}/client/v4/zones/${zoneId}${endpoint}`, {
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
      await this.fetchApi(config, "");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const zoneId = config.extra?.zoneId || "default";

    const rules = await this.fetchApi(config, "/firewall/rules").catch(() => ({ result: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cloudflare-waf-rules",
      timestamp: now,
      hash: hashEvidence(rules),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `cloudflare/${zoneId}/firewall-rules`,
      status: (rules.result as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { firewallRules: (rules.result as unknown[])?.length || 0 },
      metadata: { zoneId },
    });

    const ssl = await this.fetchApi(config, "/settings/ssl").catch(() => ({ result: { value: "off" } }));
    const sslResult = ssl as Record<string, unknown>;
    const sslVal = (sslResult.result as Record<string, unknown>)?.value ?? "unknown";
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cloudflare-ssl",
      timestamp: now,
      hash: hashEvidence(ssl),
      framework: "PCI_DSS",
      controlId: "4.1",
      source: `cloudflare/${zoneId}/ssl`,
      status: sslVal !== "off" ? "compliant" : "non_compliant",
      data: { sslMode: sslVal },
      metadata: { zoneId },
    });

    return artifacts;
  }
}
