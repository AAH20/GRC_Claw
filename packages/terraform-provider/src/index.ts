export { TerraformProvider } from "./TerraformProvider.js";
export type {
  TerraformResourceType,
  TerraformDataSourceType,
  TerraformPlanAction,
  TerraformHealthStatus,
  TerraformResourceConfig,
  TerraformResourceState,
  TerraformDiff,
  TerraformPlan,
  TerraformApplyResult,
  FrameworkResource,
  ControlResource,
  EvidenceResource,
  RiskResource,
  AgentPolicyResource,
  AgentPolicyRule,
} from "./types.js";
export { calculateRiskScore } from "./resources/risk.js";
