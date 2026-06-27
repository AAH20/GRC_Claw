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
    id: "s3-encryption",
    name: "Bucket Encryption",
    description: "Fetch S3 bucket default encryption configuration",
    evidenceCategories: ["encryption"],
  },
  {
    id: "s3-versioning",
    name: "Bucket Versioning",
    description: "Fetch S3 bucket versioning status",
    evidenceCategories: ["data_protection"],
  },
  {
    id: "s3-logging",
    name: "Bucket Access Logging",
    description: "Fetch S3 bucket server access logging configuration",
    evidenceCategories: ["logging"],
  },
];

export class AWSS3Connector implements IntegrationConnector {
  readonly id = "aws-s3";
  readonly name = "AWS S3";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "PCI_DSS",
  ];

  private async fetchS3(
    config: ConnectorConfig,
    bucket: string,
    action: string
  ): Promise<Record<string, unknown>> {
    const region = config.region || "us-east-1";
    const resp = await fetch(`https://${bucket}.s3.${region}.amazonaws.com/?${action}`, {
      headers: {
        Authorization: `AWS4-HMAC-SHA256 Credential=${config.apiToken}/${region}/s3/aws4_request`,
        "X-Amz-Date": new Date().toISOString().replace(/[:-]|\.\d{3}/g, ""),
      },
    });
    if (!resp.ok) throw new Error(`S3 ${action} failed: ${resp.status}`);
    const text = await resp.text();
    return { raw: text };
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const bucket = config.extra?.bucket || "test-bucket";
      await this.fetchS3(config, bucket, "list-type=2&max-keys=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const bucket = config.extra?.bucket || "main-bucket";

    const encryption = await this.fetchS3(config, bucket, "encryption").catch(() => ({
      enabled: false,
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "s3-encryption",
      timestamp: now,
      hash: hashEvidence(encryption),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `s3://${bucket}/encryption`,
      status: encryption.enabled !== false ? "compliant" : "non_compliant",
      data: { bucket, encryption },
      metadata: { region: config.region || "us-east-1" },
    });

    const versioning = await this.fetchS3(config, bucket, "versioning").catch(() => ({
      status: "Suspended",
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "s3-versioning",
      timestamp: now,
      hash: hashEvidence(versioning),
      framework: "ISO27001",
      controlId: "A.12.3.1",
      source: `s3://${bucket}/versioning`,
      status: versioning.status === "Enabled" ? "compliant" : "non_compliant",
      data: { bucket, versioning },
      metadata: { region: config.region || "us-east-1" },
    });

    const logging = await this.fetchS3(config, bucket, "logging").catch(() => ({
      enabled: false,
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "s3-logging",
      timestamp: now,
      hash: hashEvidence(logging),
      framework: "SOC2",
      controlId: "CC7.1",
      source: `s3://${bucket}/logging`,
      status: logging.enabled !== false ? "compliant" : "non_compliant",
      data: { bucket, logging },
      metadata: { region: config.region || "us-east-1" },
    });

    return artifacts;
  }
}
