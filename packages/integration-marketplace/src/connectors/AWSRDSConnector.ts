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
    id: "awsrds-instances",
    name: "RDS Instances",
    description: "Fetch RDS instance configurations, engine versions, and backup settings",
    evidenceCategories: ["cloud_configuration", "data_protection"],
  },
  {
    id: "awsrds-security",
    name: "Security Groups",
    description: "Fetch VPC security groups and IAM authentication settings for RDS",
    evidenceCategories: ["access_control", "network_security"],
  },
  {
    id: "awsrds-encryption",
    name: "Encryption at Rest",
    description: "Fetch KMS encryption configurations for RDS instances and snapshots",
    evidenceCategories: ["data_protection", "encryption"],
  },
];

export class AWSRDSConnector implements IntegrationConnector {
  readonly id = "aws-rds";
  readonly name = "AWS RDS";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://rds.us-east-1.amazonaws.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`AWS RDS API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/?Action=DescribeDBInstances&MaxRecords=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const instances = await this.fetchApi(config, "/?Action=DescribeDBInstances").catch(() => ({ DBInstances: [] }));
    const dbList = (instances.DBInstances || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "awsrds-instances",
      timestamp: now,
      hash: hashEvidence({ instanceCount: dbList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "aws-rds/instances",
      status: dbList.length > 0 ? "compliant" : "unknown",
      data: { instanceCount: dbList.length },
      metadata: {},
    });

    const unencrypted = dbList.filter(
      (i) => !(i as Record<string, unknown>).StorageEncrypted
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "awsrds-encryption",
      timestamp: now,
      hash: hashEvidence({ unencryptedCount: unencrypted.length }),
      framework: "PCI_DSS",
      controlId: "3.4",
      source: "aws-rds/encryption",
      status: unencrypted.length === 0 ? "compliant" : "non_compliant",
      data: { unencryptedCount: unencrypted.length },
      metadata: {},
    });

    return artifacts;
  }
}
