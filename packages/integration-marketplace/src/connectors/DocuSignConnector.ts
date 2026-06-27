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
    id: "docusign-templates",
    name: "Envelope Templates",
    description: "Fetch document templates and signing configurations",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "docusign-security",
    name: "Security Policies",
    description: "Fetch access codes, identity verification, and authentication settings",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "docusign-audit",
    name: "Envelope History",
    description: "Fetch signing ceremony audit trails and completion logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
  {
    id: "docusign-admin",
    name: "Admin Users",
    description: "Fetch admin user permissions and group memberships",
    evidenceCategories: ["access_control", "configuration"],
  },
];

export class DocuSignConnector implements IntegrationConnector {
  readonly id = "docusign";
  readonly name = "DocuSign";
  readonly category = "finance" as const;
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
    const base = config.baseUrl || "https://demo.docusign.net";
    const resp = await fetch(`${base}/restapi/v2.1${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`DocuSign API ${resp.status}: ${resp.statusText}`);
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
    const accountId = config.extra?.accountId || "";

    const templates = await this.fetchApi(
      config,
      `/accounts/${accountId}/templates`
    ).catch(() => ({ envelopeTemplates: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "docusign-templates",
      timestamp: now,
      hash: hashEvidence(templates),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `docusign/${accountId}/templates`,
      status: (templates.envelopeTemplates as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { templateCount: (templates.envelopeTemplates as unknown[])?.length || 0 },
      metadata: { accountId },
    });

    const envelopes = await this.fetchApi(
      config,
      `/accounts/${accountId}/envelopes?from_date=2024-01-01&count=10`
    ).catch(() => ({ envelopes: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "docusign-audit",
      timestamp: now,
      hash: hashEvidence(envelopes),
      framework: "ISO27001",
      controlId: "A.12.4.1",
      source: `docusign/${accountId}/envelopes`,
      status: "partial",
      data: { recentEnvelopes: (envelopes.envelopes as unknown[])?.length || 0 },
      metadata: { accountId },
    });

    return artifacts;
  }
}
