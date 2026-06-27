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
    id: "aws-iam-policies",
    name: "IAM Policies",
    description: "Fetch IAM policies, attached managed policies, and inline policies",
    evidenceCategories: ["access_control"],
  },
  {
    id: "aws-iam-access-analyzer",
    name: "IAM Access Analyzer",
    description: "Fetch Access Analyzer findings for cross-account and external access",
    evidenceCategories: ["access_control", "risk_management"],
  },
];

export class AWSIAMConnector implements IntegrationConnector {
  readonly id = "aws-iam";
  readonly name = "AWS IAM";
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

  private async fetchAws(
    config: ConnectorConfig,
    service: string,
    action: string,
    params: Record<string, string> = {}
  ): Promise<Record<string, unknown>> {
    const region = config.region || "us-east-1";
    const host = `${service}.${region}.amazonaws.com`;
    const query = new URLSearchParams({ Action: action, Version: "2010-05-08", ...params });
    const resp = await fetch(`https://${host}/?${query}`, {
      headers: {
        Authorization: `AWS4-HMAC-SHA256 Credential=${config.apiToken}/${region}/${service}/aws4_request`,
        "X-Amz-Date": new Date().toISOString().replace(/[:-]|\.\d{3}/g, ""),
      },
    });
    if (!resp.ok) throw new Error(`AWS ${service} ${resp.status}: ${resp.statusText}`);
    const text = await resp.text();
    return { raw: text };
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchAws(config, "iam", "GetCallerIdentity");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const policies = await this.fetchAws(config, "iam", "ListPolicies", {
      Scope: "Local",
    }).catch(() => ({ policies: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "aws-iam-policies",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "aws-iam/ListPolicies",
      status: "unknown",
      data: { policies },
      metadata: { region: config.region || "us-east-1" },
    });

    const analyzer = await this.fetchAws(config, "accessanalyzer", "ListFindings", {
      analyzerArn: config.extra?.analyzerArn || "",
    }).catch(() => ({ findings: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "aws-iam-access-analyzer",
      timestamp: now,
      hash: hashEvidence(analyzer),
      framework: "SOC2",
      controlId: "CC6.2",
      source: "aws-access-analyzer/ListFindings",
      status: "unknown",
      data: { findings: analyzer },
      metadata: { region: config.region || "us-east-1" },
    });

    return artifacts;
  }
}
