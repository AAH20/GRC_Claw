import type {
  ControlResource,
  TerraformHealthStatus,
  TerraformResourceState,
  TerraformDiff,
} from "../types.js";
import { randomUUID } from "node:crypto";

export function createControlResource(
  attrs: Record<string, unknown>
): ControlResource {
  return {
    id: (attrs.id as string) || randomUUID(),
    frameworkId: attrs.frameworkId as string,
    controlId: attrs.controlId as string,
    title: (attrs.title as string) || "",
    description: (attrs.description as string) || "",
    category: (attrs.category as string) || "general",
    frequency: (attrs.frequency as string) || "annual",
    automated: (attrs.automated as boolean) || false,
    status: (attrs.status as TerraformHealthStatus) || "healthy",
  };
}

export function diffControl(
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

export function validateControl(attrs: Record<string, unknown>): string[] {
  const errors: string[] = [];
  if (!attrs.frameworkId || typeof attrs.frameworkId !== "string") {
    errors.push("frameworkId is required and must be a string");
  }
  if (!attrs.controlId || typeof attrs.controlId !== "string") {
    errors.push("controlId is required and must be a string");
  }
  if (attrs.frequency && !["continuous", "daily", "weekly", "monthly", "quarterly", "annual"].includes(attrs.frequency as string)) {
    errors.push("frequency must be one of: continuous, daily, weekly, monthly, quarterly, annual");
  }
  return errors;
}
