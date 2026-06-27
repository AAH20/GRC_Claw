import type {
  TerraformResourceType,
  TerraformResourceConfig,
  TerraformResourceState,
  TerraformPlan,
  TerraformApplyResult,
  TerraformPlanAction,
  TerraformDataSourceType,
} from "./types.js";
import { randomUUID } from "node:crypto";
import {
  createFrameworkResource,
  diffFramework,
  validateFramework,
} from "./resources/framework.js";
import {
  createControlResource,
  diffControl,
  validateControl,
} from "./resources/control.js";
import {
  createEvidenceResource,
  diffEvidence,
  validateEvidence,
} from "./resources/evidence.js";
import {
  createRiskResource,
  diffRisk,
  validateRisk,
} from "./resources/risk.js";
import {
  createAgentPolicyResource,
  diffAgentPolicy,
  validateAgentPolicy,
} from "./resources/agentPolicy.js";

export class TerraformProvider {
  private stateStore: Map<string, TerraformResourceState> = new Map();
  private resourceTypes: Set<TerraformResourceType> = new Set([
    "grc_framework",
    "grc_control",
    "grc_evidence",
    "grc_risk",
    "grc_agent_policy",
  ]);

  getResourceTypes(): TerraformResourceType[] {
    return Array.from(this.resourceTypes);
  }

  getDataSourceTypes(): TerraformDataSourceType[] {
    return ["grc_controls", "grc_frameworks", "grc_evidence", "grc_risk"];
  }

  plan(config: TerraformResourceConfig): TerraformPlan {
    const existingState = this.findStateByName(config.type, config.name);
    const diffs = this.computeDiffs(config.type, existingState, config.attributes);

    return {
      resourceType: config.type,
      resourceName: config.name,
      action: existingState ? (diffs.length > 0 ? "update" : "read") : "create",
      diffs,
      beforeState: existingState ?? null,
      afterState: config.attributes,
    };
  }

  apply(config: TerraformResourceConfig): TerraformApplyResult {
    const validationErrors = this.validateResource(config);
    if (validationErrors.length > 0) {
      return {
        success: false,
        resourceId: "",
        resourceType: config.type,
        action: "create",
        state: {} as TerraformResourceState,
        timestamp: new Date().toISOString(),
      };
    }

    const existingState = this.findStateByName(config.type, config.name);
    const action: TerraformPlanAction = existingState ? "update" : "create";

    const resource = this.createResource(config.type, config.attributes);
    const state: TerraformResourceState = {
      id: (resource as Record<string, unknown>).id as string || randomUUID(),
      type: config.type,
      name: config.name,
      attributes: resource as Record<string, unknown>,
      version: (existingState?.version || 0) + 1,
      createdAt: existingState?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const stateKey = `${config.type}.${config.name}`;
    this.stateStore.set(stateKey, state);

    return {
      success: true,
      resourceId: state.id,
      resourceType: config.type,
      action,
      state,
      timestamp: state.updatedAt,
    };
  }

  destroy(resourceType: TerraformResourceType, name: string): boolean {
    const stateKey = `${resourceType}.${name}`;
    return this.stateStore.delete(stateKey);
  }

  importResource(
    resourceType: TerraformResourceType,
    name: string,
    id: string,
    attributes: Record<string, unknown>
  ): TerraformApplyResult {
    const state: TerraformResourceState = {
      id,
      type: resourceType,
      name,
      attributes,
      version: 1,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const stateKey = `${resourceType}.${name}`;
    this.stateStore.set(stateKey, state);

    return {
      success: true,
      resourceId: id,
      resourceType,
      action: "create",
      state,
      timestamp: state.updatedAt,
    };
  }

  getState(
    resourceType: TerraformResourceType,
    name: string
  ): TerraformResourceState | undefined {
    return this.findStateByName(resourceType, name);
  }

  listStates(resourceType?: TerraformResourceType): TerraformResourceState[] {
    const all = Array.from(this.stateStore.values());
    if (resourceType) {
      return all.filter((s) => s.type === resourceType);
    }
    return all;
  }

  private findStateByName(
    type: TerraformResourceType,
    name: string
  ): TerraformResourceState | undefined {
    return this.stateStore.get(`${type}.${name}`);
  }

  private computeDiffs(
    type: TerraformResourceType,
    existingState: TerraformResourceState | undefined,
    newAttrs: Record<string, unknown>
  ): import("./types.js").TerraformDiff[] {
    if (!existingState) {
      return Object.entries(newAttrs).map(([key, value]) => ({
        attribute: key,
        oldValue: undefined,
        newValue: value,
        action: "add" as const,
      }));
    }

    switch (type) {
      case "grc_framework":
        return diffFramework(existingState, newAttrs);
      case "grc_control":
        return diffControl(existingState, newAttrs);
      case "grc_evidence":
        return diffEvidence(existingState, newAttrs);
      case "grc_risk":
        return diffRisk(existingState, newAttrs);
      case "grc_agent_policy":
        return diffAgentPolicy(existingState, newAttrs);
      default:
        return [];
    }
  }

  private createResource(
    type: TerraformResourceType,
    attrs: Record<string, unknown>
  ): unknown {
    switch (type) {
      case "grc_framework":
        return createFrameworkResource(attrs);
      case "grc_control":
        return createControlResource(attrs);
      case "grc_evidence":
        return createEvidenceResource(attrs);
      case "grc_risk":
        return createRiskResource(attrs);
      case "grc_agent_policy":
        return createAgentPolicyResource(attrs);
      default:
        throw new Error(`Unknown resource type: ${type}`);
    }
  }

  private validateResource(config: TerraformResourceConfig): string[] {
    switch (config.type) {
      case "grc_framework":
        return validateFramework(config.attributes);
      case "grc_control":
        return validateControl(config.attributes);
      case "grc_evidence":
        return validateEvidence(config.attributes);
      case "grc_risk":
        return validateRisk(config.attributes);
      case "grc_agent_policy":
        return validateAgentPolicy(config.attributes);
      default:
        return [`Unknown resource type: ${config.type}`];
    }
  }
}
