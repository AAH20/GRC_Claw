import type {
  AgentPolicyResource,
  AgentPolicyRule,
  TerraformResourceState,
  TerraformDiff,
} from "../types.js";
import { randomUUID } from "node:crypto";

export function createAgentPolicyResource(
  attrs: Record<string, unknown>
): AgentPolicyResource {
  return {
    id: (attrs.id as string) || randomUUID(),
    name: attrs.name as string,
    description: (attrs.description as string) || "",
    version: (attrs.version as string) || "1.0.0",
    enabled: (attrs.enabled as boolean) !== false,
    rules: parsePolicyRules(attrs.rules as unknown[]),
    scope: (attrs.scope as string[]) || ["*"],
    schedule: (attrs.schedule as string) || "0 */6 * * *",
    maxRetries: (attrs.maxRetries as number) || 3,
    timeoutSeconds: (attrs.timeoutSeconds as number) || 300,
  };
}

function parsePolicyRules(raw: unknown[]): AgentPolicyRule[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((r, i) => {
    const rule = r as Record<string, unknown>;
    return {
      id: (rule.id as string) || randomUUID(),
      name: (rule.name as string) || `rule-${i}`,
      condition: (rule.condition as string) || "true",
      action: (rule.action as string) || "log",
      priority: (rule.priority as number) || i,
      enabled: (rule.enabled as boolean) !== false,
    };
  });
}

export function diffAgentPolicy(
  before: TerraformResourceState,
  after: Record<string, unknown>
): TerraformDiff[] {
  const diffs: TerraformDiff[] = [];
  const beforeAttrs = (before.attributes as unknown as Record<string, unknown>);

  for (const [key, newVal] of Object.entries(after)) {
    if (key === "rules") continue;
    const oldVal = beforeAttrs[key];
    if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
      diffs.push({
        attribute: key,
        oldValue: oldVal,
        newValue: newVal,
        action: oldVal === undefined ? "add" : "change",
      });
    }
  }

  const oldRules = JSON.stringify(beforeAttrs.rules || []);
  const newRules = JSON.stringify(after.rules || []);
  if (oldRules !== newRules) {
    diffs.push({
      attribute: "rules",
      oldValue: beforeAttrs.rules,
      newValue: after.rules,
      action: "change",
    });
  }

  return diffs;
}

export function validateAgentPolicy(attrs: Record<string, unknown>): string[] {
  const errors: string[] = [];
  if (!attrs.name || typeof attrs.name !== "string") {
    errors.push("name is required and must be a string");
  }
  if (attrs.maxRetries !== undefined && (typeof attrs.maxRetries !== "number" || attrs.maxRetries < 0)) {
    errors.push("maxRetries must be a non-negative number");
  }
  if (attrs.timeoutSeconds !== undefined && (typeof attrs.timeoutSeconds !== "number" || attrs.timeoutSeconds <= 0)) {
    errors.push("timeoutSeconds must be a positive number");
  }
  if (attrs.rules && !Array.isArray(attrs.rules)) {
    errors.push("rules must be an array");
  }
  return errors;
}
