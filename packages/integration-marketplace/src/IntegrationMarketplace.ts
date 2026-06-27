import type {
  IntegrationConnector,
  ConnectorConfig,
  ConnectorRegistration,
  EvidenceArtifact,
  IntegrationCategory,
  ComplianceFramework,
  MarketplaceStats,
} from "./types.js";
import {
  GitHubConnector,
  GitLabConnector,
  AWSIAMConnector,
  AWSS3Connector,
  AWSCloudTrailConnector,
  AzureADConnector,
  AzureSentinelConnector,
  GCPIAMConnector,
  GCPSCCConnector,
  OktaConnector,
  JiraConnector,
  SlackConnector,
  PagerDutyConnector,
  SnowflakeConnector,
  DatadogConnector,
  CrowdStrikeConnector,
  QualysConnector,
  SnykConnector,
  TerraformCloudConnector,
  GitHubActionsConnector,
  DockerHubConnector,
  KubernetesConnector,
  SalesforceConnector,
  HubSpotConnector,
  BambooHRConnector,
  CrowdStrikeFalconConnector,
  ServiceNowConnector,
  SplunkConnector,
  ConfluenceConnector,
  NotionConnector,
  BoxConnector,
  DropboxConnector,
  GoogleWorkspaceConnector,
  Microsoft365Connector,
  Auth0Connector,
} from "./connectors/index.js";

export interface CollectionJob {
  id: string;
  connectorId: string;
  startedAt: string;
  completedAt?: string;
  status: "running" | "completed" | "failed";
  artifacts: EvidenceArtifact[];
  error?: string;
}

export class IntegrationMarketplace {
  private registrations: Map<string, ConnectorRegistration> = new Map();
  private configs: Map<string, ConnectorConfig> = new Map();
  private jobs: CollectionJob[] = [];

  constructor() {
    this.registerBuiltinConnectors();
  }

  private registerBuiltinConnectors(): void {
    const builtins: IntegrationConnector[] = [
      new GitHubConnector(),
      new GitLabConnector(),
      new AWSIAMConnector(),
      new AWSS3Connector(),
      new AWSCloudTrailConnector(),
      new AzureADConnector(),
      new AzureSentinelConnector(),
      new GCPIAMConnector(),
      new GCPSCCConnector(),
      new OktaConnector(),
      new JiraConnector(),
      new SlackConnector(),
      new PagerDutyConnector(),
      new SnowflakeConnector(),
      new DatadogConnector(),
      new CrowdStrikeConnector(),
      new QualysConnector(),
      new SnykConnector(),
      new TerraformCloudConnector(),
      new GitHubActionsConnector(),
      new DockerHubConnector(),
      new KubernetesConnector(),
      new SalesforceConnector(),
      new HubSpotConnector(),
      new BambooHRConnector(),
      new CrowdStrikeFalconConnector(),
      new ServiceNowConnector(),
      new SplunkConnector(),
      new ConfluenceConnector(),
      new NotionConnector(),
      new BoxConnector(),
      new DropboxConnector(),
      new GoogleWorkspaceConnector(),
      new Microsoft365Connector(),
      new Auth0Connector(),
    ];
    for (const connector of builtins) {
      this.registrations.set(connector.id, {
        connector,
        enabled: true,
        errorCount: 0,
      });
    }
  }

  registerConnector(connector: IntegrationConnector): void {
    this.registrations.set(connector.id, {
      connector,
      enabled: true,
      errorCount: 0,
    });
  }

  unregisterConnector(connectorId: string): boolean {
    return this.registrations.delete(connectorId);
  }

  enableConnector(connectorId: string): void {
    const reg = this.registrations.get(connectorId);
    if (reg) reg.enabled = true;
  }

  disableConnector(connectorId: string): void {
    const reg = this.registrations.get(connectorId);
    if (reg) reg.enabled = false;
  }

  setConfig(connectorId: string, config: ConnectorConfig): void {
    this.configs.set(connectorId, config);
  }

  getConnector(connectorId: string): IntegrationConnector | undefined {
    return this.registrations.get(connectorId)?.connector;
  }

  getEnabledConnectors(): IntegrationConnector[] {
    return Array.from(this.registrations.values())
      .filter((r) => r.enabled)
      .map((r) => r.connector);
  }

  getConnectorsByCategory(category: IntegrationCategory): IntegrationConnector[] {
    return this.getEnabledConnectors().filter((c) => c.category === category);
  }

  getConnectorsByFramework(framework: ComplianceFramework): IntegrationConnector[] {
    return this.getEnabledConnectors().filter((c) => c.frameworks.includes(framework));
  }

  async testAllConnections(): Promise<Map<string, boolean>> {
    const results = new Map<string, boolean>();
    for (const [id, reg] of this.registrations) {
      if (reg.enabled) {
        const config = this.configs.get(id);
        if (config) {
          try {
            results.set(id, await reg.connector.testConnection(config));
          } catch {
            results.set(id, false);
          }
        } else {
          results.set(id, false);
        }
      }
    }
    return results;
  }

  async collectFromConnector(connectorId: string): Promise<CollectionJob> {
    const reg = this.registrations.get(connectorId);
    if (!reg) throw new Error(`Connector not found: ${connectorId}`);
    const config = this.configs.get(connectorId);
    if (!config) throw new Error(`No config for connector: ${connectorId}`);

    const job: CollectionJob = {
      id: `job-${Date.now()}-${connectorId}`,
      connectorId,
      startedAt: new Date().toISOString(),
      status: "running",
      artifacts: [],
    };
    this.jobs.push(job);

    try {
      job.artifacts = await reg.connector.collectEvidence(config);
      job.status = "completed";
      job.completedAt = new Date().toISOString();
      reg.lastCollectedAt = job.completedAt;
      reg.errorCount = 0;
    } catch (err) {
      job.status = "failed";
      job.completedAt = new Date().toISOString();
      job.error = err instanceof Error ? err.message : String(err);
      reg.errorCount++;
    }

    return job;
  }

  async collectAll(): Promise<CollectionJob[]> {
    const jobs: CollectionJob[] = [];
    for (const reg of this.registrations.values()) {
      if (reg.enabled && this.configs.has(reg.connector.id)) {
        jobs.push(await this.collectFromConnector(reg.connector.id));
      }
    }
    return jobs;
  }

  getStats(): MarketplaceStats {
    const connectors = this.getEnabledConnectors();
    const byCategory: Record<string, number> = {};
    const allFrameworks = new Set<ComplianceFramework>();
    let totalCapabilities = 0;

    for (const c of connectors) {
      byCategory[c.category] = (byCategory[c.category] || 0) + 1;
      totalCapabilities += c.capabilities.length;
      for (const f of c.frameworks) allFrameworks.add(f);
    }

    return {
      totalConnectors: connectors.length,
      connectorsByCategory: byCategory as Record<IntegrationCategory, number>,
      totalCapabilities,
      frameworksSupported: Array.from(allFrameworks),
    };
  }

  getJobs(): CollectionJob[] {
    return [...this.jobs];
  }

  getRecentJobs(limit = 10): CollectionJob[] {
    return this.jobs.slice(-limit);
  }
}
