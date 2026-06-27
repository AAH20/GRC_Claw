import type {
  FrameworkResource,
  TerraformHealthStatus,
  TerraformResourceState,
  TerraformDiff,
} from "../types.js";
import { randomUUID } from "node:crypto";

export function createFrameworkResource(
  attrs: Record<string, unknown>
): FrameworkResource {
  return {
    id: (attrs.id as string) || randomUUID(),
    name: attrs.name as string,
    version: (attrs.version as string) || "1.0.0",
    description: (attrs.description as string) || "",
    controls: (attrs.controls as string[]) || [],
    status: (attrs.status as TerraformHealthStatus) || "healthy",
    metadata: (attrs.metadata as Record<string, string>) || {},
  };
}

export function diffFramework(
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

export function validateFramework(attrs: Record<string, unknown>): string[] {
  const errors: string[] = [];
  if (!attrs.name || typeof attrs.name !== "string") {
    errors.push("name is required and must be a string");
  }
  if (attrs.version && typeof attrs.version !== "string") {
    errors.push("version must be a string");
  }
  if (attrs.controls && !Array.isArray(attrs.controls)) {
    errors.push("controls must be an array of control IDs");
  }
  return errors;
}
