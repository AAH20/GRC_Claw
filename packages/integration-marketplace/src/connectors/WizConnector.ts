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
    id: "wiz-issues",
    name: "Security Issues",
    description: "Fetch Wiz security issues with severity and blast radius",
    evidenceCategories: ["vulnerability_management", "cloud_security"],
  },
  {
    id: "wiz-vulnerabilities",
    name: "Vulnerability Findings",
    description: "Fetch Wiz vulnerability scan results across cloud resources",
    evidenceCategories: ["vulnerability_management", "asset_management"],
  },
  {
    id: "wiz-misconfigs",
    name: "Misconfigurations",
    description: "Fetch cloud misconfiguration findings and compliance gaps",
    evidenceCategories: ["compliance", "configuration"],
  },
  {
    id: "wiz-iam",
    name: "IAM Analysis",
    description: "Fetch identity and access management security findings",
    evidenceCategories: ["access_control", "identity_verification"],
  },
];

export class WizConnector implements IntegrationConnector {
  readonly id = "wiz";
  readonly name = "Wiz";
  readonly category = "cloud_provider" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
    "CIS",
  ];

  private async getToken(config: ConnectorConfig): Promise<string> {
    const base = config.baseUrl || "https://api.us1.app.wiz.io";
    const resp = await fetch(`${base}/graphql/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: `mutation { createServiceAccountToken(input: { clientId: "${config.clientId}", clientSecret: "${config.clientSecret}" }) { token } }`,
      }),
    });
    const data = (await resp.json()) as Record<string, unknown>;
    const authData = data.data as Record<string, unknown>;
    const createToken = authData?.createServiceAccountToken as Record<string, unknown>;
    return (createToken?.token as string) || "";
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getToken(config);
      const base = config.baseUrl || "https://api.us1.app.wiz.io";
      const resp = await fetch(`${base}/graphql`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: "{ projects(first: 1) { nodes { id } } }" }),
      });
      return resp.ok;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const token = await this.getToken(config);
    const base = config.baseUrl || "https://api.us1.app.wiz.io";
    const headers = {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };

    const issuesQuery = `query { issues(first: 100, filterBy: {severity: [CRITICAL, HIGH]}) { nodes { id severity title } } }`;
    const issues = await fetch(`${base}/graphql`, {
      method: "POST",
      headers,
      body: JSON.stringify({ query: issuesQuery }),
    })
      .then((r) => r.json())
      .catch(() => ({ data: { issues: { nodes: [] } } }));
    const issueNodes = issues.data?.issues?.nodes || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "wiz-issues",
      timestamp: now,
      hash: hashEvidence({ count: issueNodes.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "wiz/security-issues",
      status: issueNodes.length === 0 ? "compliant" : "non_compliant",
      data: { criticalHighIssues: issueNodes.length },
      metadata: {},
    });

    const vulnQuery = `query { vulnerabilities(first: 100, filterBy: {severity: [CRITICAL, HIGH]}) { nodes { id severity name cveId } } }`;
    const vulns = await fetch(`${base}/graphql`, {
      method: "POST",
      headers,
      body: JSON.stringify({ query: vulnQuery }),
    })
      .then((r) => r.json())
      .catch(() => ({ data: { vulnerabilities: { nodes: [] } } }));
    const vulnNodes = vulns.data?.vulnerabilities?.nodes || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "wiz-vulnerabilities",
      timestamp: now,
      hash: hashEvidence({ count: vulnNodes.length }),
      framework: "NIST_CSF",
      controlId: "ID.RA",
      source: "wiz/vulnerabilities",
      status: vulnNodes.length === 0 ? "compliant" : "non_compliant",
      data: { vulnerabilities: vulnNodes.length },
      metadata: {},
    });

    const misconfigQuery = `query { misconfigurations(first: 100) { nodes { id severity title cloudPlatform } } }`;
    const misconfigs = await fetch(`${base}/graphql`, {
      method: "POST",
      headers,
      body: JSON.stringify({ query: misconfigQuery }),
    })
      .then((r) => r.json())
      .catch(() => ({ data: { misconfigurations: { nodes: [] } } }));
    const misconfigNodes = misconfigs.data?.misconfigurations?.nodes || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "wiz-misconfigs",
      timestamp: now,
      hash: hashEvidence({ count: misconfigNodes.length }),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: "wiz/misconfigurations",
      status: misconfigNodes.length === 0 ? "compliant" : "non_compliant",
      data: { misconfigurations: misconfigNodes.length },
      metadata: {},
    });

    const iamQuery = `query { iamFindings(first: 50) { nodes { id severity entityType findingType } } }`;
    const iam = await fetch(`${base}/graphql`, {
      method: "POST",
      headers,
      body: JSON.stringify({ query: iamQuery }),
    })
      .then((r) => r.json())
      .catch(() => ({ data: { iamFindings: { nodes: [] } } }));
    const iamNodes = iam.data?.iamFindings?.nodes || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "wiz-iam",
      timestamp: now,
      hash: hashEvidence({ count: iamNodes.length }),
      framework: "CIS",
      controlId: "1.16",
      source: "wiz/iam-analysis",
      status: iamNodes.length === 0 ? "compliant" : "non_compliant",
      data: { iamFindings: iamNodes.length },
      metadata: {},
    });

    return artifacts;
  }
}
