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
    id: "sf-access-policies",
    name: "Access Policies",
    description: "Fetch Snowflake access policies and role hierarchy",
    evidenceCategories: ["access_control"],
  },
  {
    id: "sf-query-history",
    name: "Query History",
    description: "Fetch query history for data access auditing",
    evidenceCategories: ["audit", "data_access"],
  },
  {
    id: "sf-data-access",
    name: "Data Access Logs",
    description: "Fetch COPY history and data loading access logs",
    evidenceCategories: ["data_protection", "logging"],
  },
];

export class SnowflakeConnector implements IntegrationConnector {
  readonly id = "snowflake";
  readonly name = "Snowflake";
  readonly category = "data_warehouse" as const;
  readonly authType = "basic_auth" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "HIPAA"];

  private async querySnowflake(
    config: ConnectorConfig,
    sql: string
  ): Promise<Record<string, unknown>> {
    const account = config.extra?.account || "your-account";
    const resp = await fetch(`https://${account}.snowflakecomputing.com/api/v2/statements`, {
      method: "POST",
      headers: {
        Authorization: `Basic ${Buffer.from(`${config.clientId}:${config.apiToken}`).toString("base64")}`,
        "Content-Type": "application/json",
        "X-Snowflake-Database": config.extra?.database || "MAIN",
        "X-Snowflake-Schema": config.extra?.schema || "PUBLIC",
        "X-Snowflake-Role": config.extra?.role || "ACCOUNTADMIN",
      },
      body: JSON.stringify({ statement: sql, timeout: 30 }),
    });
    if (!resp.ok) throw new Error(`Snowflake ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.querySnowflake(config, "SELECT CURRENT_VERSION()");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const policies = await this.querySnowflake(
      config,
      "SELECT * FROM information_schema.policy_references WHERE POLICY_KIND = 'ROW_ACCESS_POLICY'"
    ).catch(() => ({ result: { rowset: [] as unknown[] } }));
    const policyRowset = ((policies.result as Record<string, unknown>)?.rowset || []) as unknown[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sf-access-policies",
      timestamp: now,
      hash: hashEvidence({ policyCount: policyRowset.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "snowflake/policy_references",
      status: "unknown",
      data: { policies: policyRowset },
      metadata: { account: config.extra?.account || "" },
    });

    const queries = await this.querySnowflake(
      config,
      "SELECT query_text, user_name, start_time FROM table(information_schema.query_history(limit => 100)) ORDER BY start_time DESC"
    ).catch(() => ({ result: { rowset: [] as unknown[] } }));
    const queryRowset = ((queries.result as Record<string, unknown>)?.rowset || []) as unknown[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sf-query-history",
      timestamp: now,
      hash: hashEvidence({ queryCount: queryRowset.length }),
      framework: "SOC2",
      controlId: "CC7.1",
      source: "snowflake/query_history",
      status: "unknown",
      data: { queryCount: queryRowset.length },
      metadata: { account: config.extra?.account || "" },
    });

    const copyHistory = await this.querySnowflake(
      config,
      "SELECT * FROM table(information_schema.copy_history(table_name => '%%', start_time => dateadd(day, -7, current_timestamp())))"
    ).catch(() => ({ result: { rowset: [] as unknown[] } }));
    const copyRowset = ((copyHistory.result as Record<string, unknown>)?.rowset || []) as unknown[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sf-data-access",
      timestamp: now,
      hash: hashEvidence({ copyOperations: copyRowset.length }),
      framework: "ISO27001",
      controlId: "A.12.4.1",
      source: "snowflake/copy_history",
      status: "unknown",
      data: { copyOperations: copyRowset.length },
      metadata: { account: config.extra?.account || "" },
    });

    return artifacts;
  }
}
