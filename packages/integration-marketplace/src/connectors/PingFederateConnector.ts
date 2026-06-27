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
    id: "pingfederate-sso",
    name: "SSO Configuration",
    description: "Fetch SAML/OIDC IdP configurations and SP partnerships",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "pingfederate-policies",
    name: "Authentication Policies",
    description: "Fetch authentication policy contracts and mappings",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "pingfederate-mfa",
    name: "MFA Configuration",
    description: "Fetch multi-factor authentication adapter settings",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "pingfederate-tokens",
    name: "Token Management",
    description: "Fetch OAuth token exchange and JWT settings",
    evidenceCategories: ["access_control", "monitoring"],
  },
];

export class PingFederateConnector implements IntegrationConnector {
  readonly id = "pingfederate";
  readonly name = "Ping Identity PingFederate";
  readonly category = "identity" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "PCI_DSS",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://pingfederate.example.com";
    const resp = await fetch(`${base}/pf-admin-api/v1${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`PingFederate API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/version/info");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const idpAdapters = await this.fetchApi(config, "/idp/adapters").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "pingfederate-sso",
      timestamp: now,
      hash: hashEvidence(idpAdapters),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "pingfederate/idp-adapters",
      status: (idpAdapters.items as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { idpAdapterCount: (idpAdapters.items as unknown[])?.length || 0 },
      metadata: {},
    });

    const spConnections = await this.fetchApi(config, "/idp/spConnections").catch(() => ({
      items: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "pingfederate-policies",
      timestamp: now,
      hash: hashEvidence(spConnections),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "pingfederate/sp-connections",
      status: (spConnections.items as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { spConnectionCount: (spConnections.items as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
