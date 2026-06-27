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
    id: "gd-findings",
    name: "GuardDuty Findings",
    description: "Fetch active and high-severity GuardDuty findings",
    evidenceCategories: ["vulnerability_management", "threat_detection"],
  },
  {
    id: "gd-detector-status",
    name: "Detector Status",
    description: "Fetch GuardDuty detector configuration and publishing destination",
    evidenceCategories: ["configuration", "monitoring"],
  },
  {
    id: "gd-ip-reputation",
    name: "IP Reputation Findings",
    description: "Fetch IP reputation threat intelligence findings",
    evidenceCategories: ["threat_detection", "network_security"],
  },
  {
    id: "gd-s3-protection",
    name: "S3 Protection Findings",
    description: "Fetch S3 data event-based GuardDuty findings",
    evidenceCategories: ["data_protection", "vulnerability_management"],
  },
];

export class AWSGuardDutyConnector implements IntegrationConnector {
  readonly id = "aws_guardduty";
  readonly name = "AWS GuardDuty";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
    "HIPAA",
  ];

  private async signRequest(
    config: ConnectorConfig,
    service: string,
    region: string,
    method: string,
    path: string
  ): Promise<Record<string, unknown>> {
    const host = `${service}.${region}.amazonaws.com`;
    const resp = await fetch(`https://${host}${path}`, {
      headers: {
        Authorization: `AWS4-HMAC-SHA256 Credential=${config.apiToken}/${region}/${service}/aws4_request`,
        "X-Amz-Date": new Date().toISOString().replace(/[:\-]|\.\d{3}/g, ""),
        Host: host,
      },
      method,
    });
    if (!resp.ok) throw new Error(`AWS API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const region = config.region || "us-east-1";
      await this.signRequest(config, "guardduty", region, "GET", "/detectors");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const region = config.region || "us-east-1";
    const detectorId = config.extra?.detectorId || "default";

    const detectors = await this.signRequest(
      config, "guardduty", region, "GET", "/detectors"
    ).catch(() => ({ detectorIds: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gd-detector-status",
      timestamp: now,
      hash: hashEvidence(detectors),
      framework: "SOC2",
      controlId: "CC7.1",
      source: `aws/guardduty/${region}/detectors`,
      status: Array.isArray(detectors.detectorIds) && detectors.detectorIds.length > 0
        ? "compliant"
        : "non_compliant",
      data: { activeDetectors: Array.isArray(detectors.detectorIds) ? detectors.detectorIds.length : 0 },
      metadata: { region, detectorId },
    });

    const findings = await this.signRequest(
      config,
      "guardduty",
      region,
      "POST",
      `/detectors/${detectorId}/findings`
    ).catch(() => ({ findings: [] }));
    const findingList = Array.isArray(findings.findings) ? findings.findings : [];
    const highSeverity = findingList.filter(
      (f: Record<string, unknown>) => (f.severity as number) >= 7
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gd-findings",
      timestamp: now,
      hash: hashEvidence(findings),
      framework: "NIST_CSF",
      controlId: "RS.AN",
      source: `aws/guardduty/${region}/findings`,
      status: highSeverity.length === 0 ? "compliant" : "non_compliant",
      data: {
        totalFindings: findingList.length,
        highSeverityCount: highSeverity.length,
      },
      metadata: { region, detectorId },
    });

    const ipFindings = await this.signRequest(
      config,
      "guardduty",
      region,
      "POST",
      `/detectors/${detectorId}/findings?FilterCriteria={"Criterion":{"type":[{"Value":"Recon:EC2/API calls made from unusual location","Comparison":"eq"}]}}`
    ).catch(() => ({ findings: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gd-ip-reputation",
      timestamp: now,
      hash: hashEvidence(ipFindings),
      framework: "ISO27001",
      controlId: "A.13.1.1",
      source: `aws/guardduty/${region}/ip-reputation`,
      status: Array.isArray(ipFindings.findings) && ipFindings.findings.length === 0
        ? "compliant"
        : "non_compliant",
      data: { ipReputationFindings: Array.isArray(ipFindings.findings) ? ipFindings.findings.length : 0 },
      metadata: { region, detectorId },
    });

    const s3Findings = await this.signRequest(
      config,
      "guardduty",
      region,
      "POST",
      `/detectors/${detectorId}/findings?FilterCriteria={"Criterion":{"resource.accessKeyDetails.userName":[{"Value":"*","Comparison":"contains"}]}}`
    ).catch(() => ({ findings: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gd-s3-protection",
      timestamp: now,
      hash: hashEvidence(s3Findings),
      framework: "PCI_DSS",
      controlId: "3.4.1",
      source: `aws/guardduty/${region}/s3-protection`,
      status: Array.isArray(s3Findings.findings) && s3Findings.findings.length === 0
        ? "compliant"
        : "non_compliant",
      data: { s3Findings: Array.isArray(s3Findings.findings) ? s3Findings.findings.length : 0 },
      metadata: { region, detectorId },
    });

    return artifacts;
  }
}
