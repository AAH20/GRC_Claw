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
    id: "az-policy-compliance",
    name: "Policy Compliance State",
    description: "Fetch Azure Policy compliance state per scope",
    evidenceCategories: ["compliance", "configuration"],
  },
  {
    id: "az-policy-assignments",
    name: "Policy Assignments",
    description: "Fetch assigned policies and initiatives across management groups",
    evidenceCategories: ["configuration", "access_control"],
  },
  {
    id: "az-policy-remediation",
    name: "Remediation Tasks",
    description: "Fetch policy remediation task status and non-compliant resources",
    evidenceCategories: ["change_management", "compliance"],
  },
  {
    id: "az-policy-deny",
    name: "Deny Effect Evaluations",
    description: "Fetch deny-effect policy evaluation results",
    evidenceCategories: ["access_control", "configuration"],
  },
];

export class AzurePolicyConnector implements IntegrationConnector {
  readonly id = "azure_policy";
  readonly name = "Azure Policy";
  readonly category = "cloud_provider" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "CIS",
  ];

  private async getToken(config: ConnectorConfig): Promise<string> {
    if (config.apiToken) return config.apiToken;
    const resp = await fetch(
      `https://login.microsoftonline.com/${config.tenantId}/oauth2/v2.0/token`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "client_credentials",
          client_id: config.clientId || "",
          client_secret: config.clientSecret || "",
          scope: "https://management.azure.com/.default",
        }),
      }
    );
    const data = (await resp.json()) as Record<string, unknown>;
    return data.access_token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getToken(config);
      const resp = await fetch(
        "https://management.azure.com/subscriptions?api-version=2020-01-01",
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return resp.ok;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const token = await this.getToken(config);
    const subscriptionId = config.extra?.subscriptionId || "default";
    const scope = `/subscriptions/${subscriptionId}`;

    const complianceState = await fetch(
      `https://management.azure.com${scope}/providers/Microsoft.PolicyInsights/policyStates/latest/summarizeByPolicyGroup?api-version=2021-10-01`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => r.json())
      .catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "az-policy-compliance",
      timestamp: now,
      hash: hashEvidence(complianceState as Record<string, unknown>),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `azure/policy/${subscriptionId}/compliance`,
      status: "compliant",
      data: { policyGroups: Array.isArray(complianceState.value) ? complianceState.value.length : 0 },
      metadata: { subscriptionId },
    });

    const assignments = await fetch(
      `https://management.azure.com${scope}/providers/Microsoft.Authorization/policyAssignments?api-version=2021-06-01`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => r.json())
      .catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "az-policy-assignments",
      timestamp: now,
      hash: hashEvidence(assignments as Record<string, unknown>),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: `azure/policy/${subscriptionId}/assignments`,
      status: Array.isArray(assignments.value) && assignments.value.length > 0
        ? "compliant"
        : "partial",
      data: { assignmentCount: Array.isArray(assignments.value) ? assignments.value.length : 0 },
      metadata: { subscriptionId },
    });

    const remediations = await fetch(
      `https://management.azure.com${scope}/providers/Microsoft.PolicyInsights/remediations?api-version=2021-10-01`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => r.json())
      .catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "az-policy-remediation",
      timestamp: now,
      hash: hashEvidence(remediations as Record<string, unknown>),
      framework: "NIST_CSF",
      controlId: "ID.RA",
      source: `azure/policy/${subscriptionId}/remediations`,
      status: "compliant",
      data: { remediationCount: Array.isArray(remediations.value) ? remediations.value.length : 0 },
      metadata: { subscriptionId },
    });

    const denyEvaluations = await fetch(
      `https://management.azure.com${scope}/providers/Microsoft.PolicyInsights/policyStates/latest/summarize?api-version=2021-10-01&$filter=PolicyDefinitionAction%20eq%20'deny'`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => r.json())
      .catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "az-policy-deny",
      timestamp: now,
      hash: hashEvidence(denyEvaluations as Record<string, unknown>),
      framework: "CIS",
      controlId: "2.1",
      source: `azure/policy/${subscriptionId}/deny-evaluations`,
      status: "compliant",
      data: { evaluationCount: Array.isArray(denyEvaluations.value) ? denyEvaluations.value.length : 0 },
      metadata: { subscriptionId },
    });

    return artifacts;
  }
}
