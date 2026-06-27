import type {
  RiskResource,
  TerraformResourceState,
  TerraformDiff,
} from "../types.js";
import { randomUUID } from "node:crypto";

const RISK_SCORES: Record<string, Record<string, number>> = {
  low: { low: 1, medium: 2, high: 3, critical: 4 },
  medium: { low: 2, medium: 4, high: 6, critical: 8 },
  high: { low: 3, medium: 6, high: 9, critical: 12 },
  critical: { low: 4, medium: 8, high: 12, critical: 16 },
};

export function calculateRiskScore(
  likelihood: string,
  impact: string
): number {
  return RISK_SCORES[likelihood]?.[impact] ?? 0;
}

export function createRiskResource(
  attrs: Record<string, unknown>
): RiskResource {
  const likelihood = (attrs.likelihood as string) || "medium";
  const impact = (attrs.impact as string) || "medium";

  return {
    id: (attrs.id as string) || randomUUID(),
    title: attrs.title as string,
    description: (attrs.description as string) || "",
    likelihood: likelihood as RiskResource["likelihood"],
    impact: impact as RiskResource["impact"],
    score: (attrs.score as number) || calculateRiskScore(likelihood, impact),
    owner: (attrs.owner as string) || "",
    status: (attrs.status as RiskResource["status"]) || "open",
    mitigationPlan: (attrs.mitigationPlan as string) || "",
    controls: (attrs.controls as string[]) || [],
  };
}

export function diffRisk(
  before: TerraformResourceState,
  after: Record<string, unknown>
): TerraformDiff[] {
  const diffs: TerraformDiff[] = [];
  const beforeAttrs = (before.attributes as unknown as Record<string, unknown>);

  for (const [key, newVal] of Object.entries(after)) {
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

  for (const key of Object.keys(beforeAttrs)) {
    if (!(key in after)) {
      diffs.push({
        attribute: key,
        oldValue: beforeAttrs[key],
        newValue: undefined,
        action: "remove",
      });
    }
  }

  return diffs;
}

export function validateRisk(attrs: Record<string, unknown>): string[] {
  const errors: string[] = [];
  if (!attrs.title || typeof attrs.title !== "string") {
    errors.push("title is required and must be a string");
  }
  if (attrs.likelihood && !["low", "medium", "high", "critical"].includes(attrs.likelihood as string)) {
    errors.push("likelihood must be one of: low, medium, high, critical");
  }
  if (attrs.impact && !["low", "medium", "high", "critical"].includes(attrs.impact as string)) {
    errors.push("impact must be one of: low, medium, high, critical");
  }
  if (attrs.status && !["open", "mitigated", "accepted", "closed"].includes(attrs.status as string)) {
    errors.push("status must be one of: open, mitigated, accepted, closed");
  }
  return errors;
}
