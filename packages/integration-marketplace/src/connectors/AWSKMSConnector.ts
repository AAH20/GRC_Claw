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
    id: "awskms-keys",
    name: "KMS Keys",
    description: "Fetch KMS key configurations, rotation policies, and usage",
    evidenceCategories: ["encryption", "configuration"],
  },
  {
    id: "awskms-access",
    name: "Key Access Controls",
    description: "Fetch key policies and grants controlling access to KMS keys",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "awskms-audit",
    name: "Key Audit Trail",
    description: "Fetch CloudTrail events for KMS key usage and management",
    evidenceCategories: ["monitoring", "audit"],
  },
];

export class AWSKMSConnector implements IntegrationConnector {
  readonly id = "aws-kms";
  readonly name = "AWS KMS";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://kms.us-east-1.amazonaws.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`AWS KMS API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/?Action=ListKeys&Limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const keys = await this.fetchApi(config, "/?Action=ListKeys").catch(() => ({ Keys: [] }));
    const keyList = (keys.Keys || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "awskms-keys",
      timestamp: now,
      hash: hashEvidence({ keyCount: keyList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "aws-kms/keys",
      status: keyList.length > 0 ? "compliant" : "unknown",
      data: { keyCount: keyList.length },
      metadata: {},
    });

    return artifacts;
  }
}
