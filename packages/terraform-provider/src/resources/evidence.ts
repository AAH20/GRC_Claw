import type {
  EvidenceResource,
  TerraformResourceState,
  TerraformDiff,
} from "../types.js";
import { createHash, randomUUID } from "node:crypto";

export function createEvidenceResource(
  attrs: Record<string, unknown>
): EvidenceResource {
  const data = (attrs.data as Record<string, unknown>) || {};
  const hash = `sha256:${createHash("sha256").update(JSON.stringify(data)).digest("hex")}`;

  return {
    id: (attrs.id as string) || `ev-${randomUUID()}`,
    controlId: attrs.controlId as string,
    connectorId: attrs.connectorId as string,
    capabilityId: attrs.capabilityId as string,
    timestamp: (attrs.timestamp as string) || new Date().toISOString(),
    hash: (attrs.hash as string) || hash,
    framework: (attrs.framework as string) || "SOC2",
    source: (attrs.source as string) || "",
    status: (attrs.status as EvidenceResource["status"]) || "unknown",
    data,
  };
}

export function diffEvidence(
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

export function validateEvidence(attrs: Record<string, unknown>): string[] {
  const errors: string[] = [];
  if (!attrs.controlId || typeof attrs.controlId !== "string") {
    errors.push("controlId is required");
  }
  if (!attrs.connectorId || typeof attrs.connectorId !== "string") {
    errors.push("connectorId is required");
  }
  if (attrs.status && !["compliant", "non_compliant", "partial", "unknown"].includes(attrs.status as string)) {
    errors.push("status must be one of: compliant, non_compliant, partial, unknown");
  }
  return errors;
}
