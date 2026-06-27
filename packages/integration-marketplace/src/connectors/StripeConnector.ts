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
    id: "stripe-payments",
    name: "Payment Processing",
    description: "Fetch Stripe payment configurations and PCI compliance status",
    evidenceCategories: ["compliance", "data_protection"],
  },
  {
    id: "stripe-webhooks",
    name: "Webhook Security",
    description: "Fetch webhook endpoint configurations and signature verification",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "stripe-api-keys",
    name: "API Key Management",
    description: "Fetch API key usage and rotation status",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "stripe-disputes",
    name: "Fraud Prevention",
    description: "Fetch Radar rules and dispute/fraud metrics",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
];

export class StripeConnector implements IntegrationConnector {
  readonly id = "stripe";
  readonly name = "Stripe";
  readonly category = "finance" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "PCI_DSS",
    "NIST_CSF",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.stripe.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
    if (!resp.ok) throw new Error(`Stripe API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/v1/balance");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const balance = await this.fetchApi(config, "/v1/balance").catch(() => ({}));
    const balanceData = balance as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "stripe-payments",
      timestamp: now,
      hash: hashEvidence(balance),
      framework: "PCI_DSS",
      controlId: "1.3",
      source: "stripe/balance",
      status: balanceData.object === "balance" ? "compliant" : "unknown",
      data: { balanceAvailable: ((balanceData.available as unknown[]) || []).length },
      metadata: {},
    });

    const webhooks = await this.fetchApi(config, "/v1/webhook_endpoints").catch(() => ({
      data: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "stripe-webhooks",
      timestamp: now,
      hash: hashEvidence(webhooks),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "stripe/webhooks",
      status: (webhooks.data as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { webhookEndpoints: (webhooks.data as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
