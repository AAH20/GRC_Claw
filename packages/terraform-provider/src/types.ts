export type TerraformResourceType =
  | "grc_framework"
  | "grc_control"
  | "grc_evidence"
  | "grc_risk"
  | "grc_agent_policy";

export type TerraformDataSourceType =
  | "grc_controls"
  | "grc_frameworks"
  | "grc_evidence"
  | "grc_risk";

export type TerraformPlanAction = "create" | "read" | "update" | "delete";

export type TerraformHealthStatus = "healthy" | "degraded" | "unhealthy";

export interface TerraformResourceConfig {
  type: TerraformResourceType;
  name: string;
  attributes: Record<string, unknown>;
}

export interface TerraformResourceState {
  id: string;
  type: TerraformResourceType;
  name: string;
  attributes: Record<string, unknown>;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface TerraformDiff {
  attribute: string;
  oldValue: unknown;
  newValue: unknown;
  action: "add" | "change" | "remove";
}

export interface TerraformPlan {
  resourceType: TerraformResourceType;
  resourceName: string;
  action: TerraformPlanAction;
  diffs: TerraformDiff[];
  beforeState: TerraformResourceState | null;
  afterState: Record<string, unknown>;
}

export interface TerraformApplyResult {
  success: boolean;
  resourceId: string;
  resourceType: TerraformResourceType;
  action: TerraformPlanAction;
  state: TerraformResourceState;
  timestamp: string;
}

export interface FrameworkResource {
  id: string;
  name: string;
  version: string;
  description: string;
  controls: string[];
  status: TerraformHealthStatus;
  metadata: Record<string, string>;
}

export interface ControlResource {
  id: string;
  frameworkId: string;
  controlId: string;
  title: string;
  description: string;
  category: string;
  frequency: string;
  automated: boolean;
  status: TerraformHealthStatus;
}

export interface EvidenceResource {
  id: string;
  controlId: string;
  connectorId: string;
  capabilityId: string;
  timestamp: string;
  hash: string;
  framework: string;
  source: string;
  status: "compliant" | "non_compliant" | "partial" | "unknown";
  data: Record<string, unknown>;
}

export interface RiskResource {
  id: string;
  title: string;
  description: string;
  likelihood: "low" | "medium" | "high" | "critical";
  impact: "low" | "medium" | "high" | "critical";
  score: number;
  owner: string;
  status: "open" | "mitigated" | "accepted" | "closed";
  mitigationPlan: string;
  controls: string[];
}

export interface AgentPolicyResource {
  id: string;
  name: string;
  description: string;
  version: string;
  enabled: boolean;
  rules: AgentPolicyRule[];
  scope: string[];
  schedule: string;
  maxRetries: number;
  timeoutSeconds: number;
}

export interface AgentPolicyRule {
  id: string;
  name: string;
  condition: string;
  action: string;
  priority: number;
  enabled: boolean;
}
