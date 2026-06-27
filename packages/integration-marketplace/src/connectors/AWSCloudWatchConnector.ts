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
    id: "cloudwatch-alarms",
    name: "CloudWatch Alarms",
    description: "Fetch CloudWatch alarm configurations and state history",
    evidenceCategories: ["monitoring", "configuration"],
  },
  {
    id: "cloudwatch-logs",
    name: "Log Groups",
    description: "Fetch CloudWatch log group retention settings and metric filters",
    evidenceCategories: ["data_protection", "monitoring"],
  },
  {
    id: "cloudwatch-dashboards",
    name: "Monitoring Dashboards",
    description: "Fetch CloudWatch dashboard definitions and metric widgets",
    evidenceCategories: ["monitoring", "configuration"],
  },
];

export class AWSCloudWatchConnector implements IntegrationConnector {
  readonly id = "aws-cloudwatch";
  readonly name = "AWS CloudWatch";
  readonly category = "monitoring" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://monitoring.us-east-1.amazonaws.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`AWS CloudWatch API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/?Action=DescribeAlarms&MaxRecords=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const alarms = await this.fetchApi(
      config,
      "/?Action=DescribeAlarms&MaxRecords=100"
    ).catch(() => ({ MetricAlarms: [] }));
    const alarmList = (alarms.MetricAlarms || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cloudwatch-alarms",
      timestamp: now,
      hash: hashEvidence({ alarmCount: alarmList.length }),
      framework: "SOC2",
      controlId: "CC7.1",
      source: "aws-cloudwatch/alarms",
      status: alarmList.length > 0 ? "compliant" : "unknown",
      data: { alarmCount: alarmList.length },
      metadata: {},
    });

    return artifacts;
  }
}
