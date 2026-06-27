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
    id: "awslambda-functions",
    name: "Lambda Functions",
    description: "Fetch AWS Lambda function configurations and runtime settings",
    evidenceCategories: ["cloud_configuration", "access_control"],
  },
  {
    id: "awslambda-permissions",
    name: "Function Permissions",
    description: "Fetch IAM execution roles and resource policies on Lambda functions",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "awslambda-logging",
    name: "Function Logging",
    description: "Fetch CloudWatch log group configurations for Lambda functions",
    evidenceCategories: ["monitoring", "configuration"],
  },
];

export class AWSLambdaConnector implements IntegrationConnector {
  readonly id = "aws-lambda";
  readonly name = "AWS Lambda";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://lambda.us-east-1.amazonaws.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`AWS Lambda API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/2015-03-31/functions/?MaxItems=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const functions = await this.fetchApi(config, "/2015-03-31/functions/?MaxItems=100").catch(() => ({ Functions: [] }));
    const funcList = (functions.Functions || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "awslambda-functions",
      timestamp: now,
      hash: hashEvidence({ functionCount: funcList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "aws-lambda/functions",
      status: funcList.length > 0 ? "compliant" : "unknown",
      data: { functionCount: funcList.length },
      metadata: {},
    });

    const publicFunctions = funcList.filter(
      (f) => (f as Record<string, unknown>).Policy !== null
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "awslambda-permissions",
      timestamp: now,
      hash: hashEvidence({ publicCount: publicFunctions.length }),
      framework: "SOC2",
      controlId: "CC6.3",
      source: "aws-lambda/permissions",
      status: publicFunctions.length === 0 ? "compliant" : "non_compliant",
      data: { publicFunctionCount: publicFunctions.length },
      metadata: {},
    });

    return artifacts;
  }
}
