import type { CloudConnector, CloudFinding, ConnectorHealth, CloudProvider, ConnectorRegistry as IConnectorRegistry } from "./types.js";
import { AwsSecurityHubConnector, AwsGuardDutyConnector } from "./providers/aws.js";
import { AzureSentinelConnector, AzureDefenderConnector } from "./providers/azure.js";
import { GcpChronicleConnector, GcpSecurityCommandCenterConnector } from "./providers/gcp.js";

export class CloudConnectorRegistry implements IConnectorRegistry {
  private connectors: Map<string, CloudConnector> = new Map();

  register(connector: CloudConnector): void {
    this.connectors.set(`${connector.provider}-${Math.random().toString(36).slice(7)}`, connector);
  }

  get(provider: CloudProvider): CloudConnector | undefined {
    return Array.from(this.connectors.values()).find((c) => c.provider === provider);
  }

  list(): CloudConnector[] {
    return Array.from(this.connectors.values());
  }

  async fetchAllFindings(): Promise<CloudFinding[]> {
    const findings: CloudFinding[] = [];
    for (const connector of this.connectors.values()) {
      try {
        const connectorFindings = await connector.fetchFindings();
        findings.push(...connectorFindings);
      } catch (error) {
        console.error(`Error fetching from ${connector.provider}:`, error);
      }
    }
    return findings;
  }

  async getHealthReport(): Promise<ConnectorHealth[]> {
    const health: ConnectorHealth[] = [];
    for (const connector of this.connectors.values()) {
      health.push(await connector.health());
    }
    return health;
  }
}

export { AwsSecurityHubConnector, AwsGuardDutyConnector } from "./providers/aws.js";
export { AzureSentinelConnector, AzureDefenderConnector } from "./providers/azure.js";
export { GcpChronicleConnector, GcpSecurityCommandCenterConnector } from "./providers/gcp.js";
export type * from "./types.js";

// Ticket & endpoint connectors
export { fetchJiraSecurityEvidence } from "./jira.js";
export type { JiraConfig, JiraEvidence } from "./jira.js";
export { fetchLinearSecurityIssues } from "./linear.js";
export type { LinearConfig, LinearEvidence } from "./linear.js";
export { fetchCrowdStrikeDetections } from "./crowdstrike.js";
export type { CrowdStrikeConfig, CsDetection } from "./crowdstrike.js";
