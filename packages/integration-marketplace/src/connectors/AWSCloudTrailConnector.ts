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
    id: "ct-audit-logs",
    name: "CloudTrail Audit Logs",
    description: "Fetch CloudTrail event history and trail configuration",
    evidenceCategories: ["logging", "audit"],
  },
];

export class AWSCloudTrailConnector implements IntegrationConnector {
  readonly id = "aws-cloudtrail";
  readonly name = "AWS CloudTrail";
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

  private async fetchCloudTrail(
    config: ConnectorConfig,
    action: string,
    params: Record<string, string> = {}
  ): Promise<Record<string, unknown>> {
    const region = config.region || "us-east-1";
    const host = `cloudtrail.${region}.amazonaws.com`;
    const query = new URLSearchParams({ Action: action, Version: "2013-11-01", ...params });
    const resp = await fetch(`https://${host}/?${query}`, {
      headers: {
        Authorization: `AWS4-HMAC-SHA256 Credential=${config.apiToken}/${region}/cloudtrail/aws4_request`,
        "X-Amz-Date": new Date().toISOString().replace(/[:-]|\.\d{3}/g, ""),
      },
    });
    if (!resp.ok) throw new Error(`CloudTrail ${resp.status}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchCloudTrail(config, "DescribeTrails");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const now = new Date().toISOString();
    const trails = await this.fetchCloudTrail(config, "DescribeTrails").catch(() => ({
      trailList: [],
    }));
    const trailList = (trails.trailList || []) as Record<string, unknown>[];

    return [
      {
        id: generateEvidenceId(),
        connectorId: this.id,
        capabilityId: "ct-audit-logs",
        timestamp: now,
        hash: hashEvidence(trails),
        framework: "SOC2",
        controlId: "CC7.1",
        source: "aws-cloudtrail/DescribeTrails",
        status: trailList.length > 0 ? "compliant" : "non_compliant",
        data: {
          trailCount: trailList.length,
          trails: trailList.map((t) => ({
            name: t.Name,
            s3BucketName: t.S3BucketName,
            isMultiRegionTrail: t.IsMultiRegionTrail,
            isOrganizationTrail: t.IsOrganizationTrail,
            logFileValidationEnabled: t.LogFileValidationEnabled,
          })),
        },
        metadata: { region: config.region || "us-east-1" },
      },
    ];
  }
}
