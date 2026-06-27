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
    id: "k8s-rbac",
    name: "RBAC Policies",
    description: "Fetch Kubernetes ClusterRole, ClusterRoleBinding, and Role data",
    evidenceCategories: ["access_control", "authorization"],
  },
  {
    id: "k8s-network-policies",
    name: "Network Policies",
    description: "Fetch Kubernetes NetworkPolicy resources",
    evidenceCategories: ["network_security"],
  },
  {
    id: "k8s-pod-security",
    name: "Pod Security",
    description: "Fetch Pod Security Standards and PSP/PSA configurations",
    evidenceCategories: ["container_security", "configuration"],
  },
];

export class KubernetesConnector implements IntegrationConnector {
  readonly id = "kubernetes";
  readonly name = "Kubernetes";
  readonly category = "infrastructure" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchK8s(
    config: ConnectorConfig,
    apiPath: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://kubernetes.default.svc";
    const resp = await fetch(`${base}${apiPath}`, {
      headers: { Authorization: `Bearer ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`K8s API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchK8s(config, "/version");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const rbac = await this.fetchK8s(config, "/apis/rbac.authorization.k8s.io/v1/clusterrolebindings").catch(() => ({
      items: [],
    }));
    const roleBindings = (rbac.items || []) as Record<string, unknown>[];
    const clusterAdminBindings = roleBindings.filter(
      (r) =>
        (r.roleRef as Record<string, unknown>)?.name === "cluster-admin"
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "k8s-rbac",
      timestamp: now,
      hash: hashEvidence({ totalBindings: roleBindings.length, clusterAdminBindings: clusterAdminBindings.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "k8s/rbac/clusterrolebindings",
      status: clusterAdminBindings.length <= 2 ? "compliant" : "partial",
      data: { totalBindings: roleBindings.length, clusterAdminBindings: clusterAdminBindings.length },
      metadata: {},
    });

    const netPol = await this.fetchK8s(config, "/apis/networking.k8s.io/v1/networkpolicies").catch(() => ({
      items: [],
    }));
    const netPolicies = (netPol.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "k8s-network-policies",
      timestamp: now,
      hash: hashEvidence({ policyCount: netPolicies.length }),
      framework: "ISO27001",
      controlId: "A.13.1.1",
      source: "k8s/networking/networkpolicies",
      status: netPolicies.length > 0 ? "compliant" : "non_compliant",
      data: { networkPolicyCount: netPolicies.length },
      metadata: {},
    });

    const pods = await this.fetchK8s(config, "/api/v1/pods").catch(() => ({ items: [] }));
    const podList = (pods.items || []) as Record<string, unknown>[];
    const privilegedPods = podList.filter((p) => {
      const containers = [
        ...(((p.spec as Record<string, unknown>)?.containers || []) as Record<string, unknown>[]),
        ...(((p.spec as Record<string, unknown>)?.initContainers || []) as Record<string, unknown>[]),
      ];
      return containers.some(
        (c) => (c.securityContext as Record<string, unknown>)?.privileged === true
      );
    });
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "k8s-pod-security",
      timestamp: now,
      hash: hashEvidence({ totalPods: podList.length, privilegedPods: privilegedPods.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "k8s/pods",
      status: privilegedPods.length === 0 ? "compliant" : "non_compliant",
      data: { totalPods: podList.length, privilegedPods: privilegedPods.length },
      metadata: {},
    });

    return artifacts;
  }
}
