import { describe, it } from "node:test";
import assert from "node:assert";
import { TerraformProvider } from "./TerraformProvider.js";
import { calculateRiskScore } from "./resources/risk.js";
import type {
  TerraformResourceConfig,
  TerraformPlan,
  TerraformApplyResult,
} from "./types.js";

describe("TerraformProvider", () => {
  it("returns resource and data source types", () => {
    const provider = new TerraformProvider();
    const resourceTypes = provider.getResourceTypes();
    assert.deepStrictEqual(resourceTypes, [
      "grc_framework",
      "grc_control",
      "grc_evidence",
      "grc_risk",
      "grc_agent_policy",
    ]);

    const dataSources = provider.getDataSourceTypes();
    assert.deepStrictEqual(dataSources, [
      "grc_controls",
      "grc_frameworks",
      "grc_evidence",
      "grc_risk",
    ]);
  });

  it("plans a create for a new framework", () => {
    const provider = new TerraformProvider();
    const config: TerraformResourceConfig = {
      type: "grc_framework",
      name: "soc2-v2",
      attributes: {
        name: "SOC 2 Type II",
        version: "2.0",
        description: "SOC 2 Type II compliance framework",
        controls: ["CC6.1", "CC6.8", "CC8.1"],
      },
    };

    const plan = provider.plan(config);
    assert.strictEqual(plan.action, "create");
    assert.strictEqual(plan.resourceType, "grc_framework");
    assert.strictEqual(plan.resourceName, "soc2-v2");
    assert.strictEqual(plan.beforeState, null);
    assert.ok(plan.diffs.length > 0);
  });

  it("applies and creates framework state", () => {
    const provider = new TerraformProvider();
    const config: TerraformResourceConfig = {
      type: "grc_framework",
      name: "soc2-v2",
      attributes: {
        name: "SOC 2 Type II",
        version: "2.0",
        description: "SOC 2 Type II compliance framework",
        controls: ["CC6.1", "CC6.8", "CC8.1"],
      },
    };

    const result = provider.apply(config);
    assert.strictEqual(result.success, true);
    assert.strictEqual(result.action, "create");
    assert.strictEqual(result.resourceType, "grc_framework");
    assert.ok(result.state.id);
    assert.strictEqual(result.state.version, 1);
    assert.strictEqual(result.state.name, "soc2-v2");
  });

  it("detects diffs on update", () => {
    const provider = new TerraformProvider();
    const config: TerraformResourceConfig = {
      type: "grc_framework",
      name: "soc2-v2",
      attributes: {
        name: "SOC 2 Type II",
        version: "2.0",
        description: "SOC 2 Type II",
        controls: ["CC6.1"],
      },
    };

    provider.apply(config);

    const updatedConfig: TerraformResourceConfig = {
      type: "grc_framework",
      name: "soc2-v2",
      attributes: {
        name: "SOC 2 Type II",
        version: "2.1",
        description: "SOC 2 Type II Updated",
        controls: ["CC6.1", "CC6.8"],
      },
    };

    const plan = provider.plan(updatedConfig);
    assert.strictEqual(plan.action, "update");
    assert.ok(plan.diffs.length > 0);
    assert.ok(plan.beforeState !== null);
  });

  it("updates state on apply with changes", () => {
    const provider = new TerraformProvider();
    const config1: TerraformResourceConfig = {
      type: "grc_framework",
      name: "soc2-v2",
      attributes: {
        name: "SOC 2",
        version: "1.0",
        controls: ["CC6.1"],
      },
    };
    provider.apply(config1);

    const config2: TerraformResourceConfig = {
      type: "grc_framework",
      name: "soc2-v2",
      attributes: {
        name: "SOC 2",
        version: "2.0",
        controls: ["CC6.1", "CC6.8"],
      },
    };
    const result = provider.apply(config2);

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.action, "update");
    assert.strictEqual(result.state.version, 2);
    assert.strictEqual(
      (result.state.attributes as Record<string, unknown>).version,
      "2.0"
    );
  });

  it("destroys a resource", () => {
    const provider = new TerraformProvider();
    provider.apply({
      type: "grc_framework",
      name: "soc2-v2",
      attributes: { name: "SOC 2" },
    });

    const destroyed = provider.destroy("grc_framework", "soc2-v2");
    assert.strictEqual(destroyed, true);
    assert.strictEqual(provider.getState("grc_framework", "soc2-v2"), undefined);
  });

  it("imports a resource", () => {
    const provider = new TerraformProvider();
    const result = provider.importResource(
      "grc_framework",
      "existing-fw",
      "fw-123",
      { name: "Existing Framework", version: "1.0" }
    );

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.resourceId, "fw-123");
    const state = provider.getState("grc_framework", "existing-fw");
    assert.ok(state);
    assert.strictEqual(state.id, "fw-123");
  });

  it("lists states filtered by type", () => {
    const provider = new TerraformProvider();
    provider.apply({
      type: "grc_framework",
      name: "fw1",
      attributes: { name: "FW1" },
    });
    provider.apply({
      type: "grc_control",
      name: "ctrl1",
      attributes: { frameworkId: "fw1", controlId: "CC6.1" },
    });

    const frameworks = provider.listStates("grc_framework");
    assert.strictEqual(frameworks.length, 1);
    assert.strictEqual(frameworks[0].type, "grc_framework");

    const all = provider.listStates();
    assert.strictEqual(all.length, 2);
  });

  it("validates resource config and rejects invalid", () => {
    const provider = new TerraformProvider();
    const result = provider.apply({
      type: "grc_framework",
      name: "invalid-fw",
      attributes: {},
    });

    assert.strictEqual(result.success, false);
  });

  it("plans read when no diffs", () => {
    const provider = new TerraformProvider();
    const attrs = { name: "SOC 2", version: "1.0", controls: ["CC6.1"] };
    provider.apply({
      type: "grc_framework",
      name: "soc2",
      attributes: attrs,
    });

    const state = provider.getState("grc_framework", "soc2")!;
    const plan = provider.plan({
      type: "grc_framework",
      name: "soc2",
      attributes: state.attributes as Record<string, unknown>,
    });

    assert.strictEqual(plan.action, "read");
    assert.strictEqual(plan.diffs.length, 0);
  });
});

describe("Risk Scoring", () => {
  it("calculates risk scores correctly", () => {
    assert.strictEqual(calculateRiskScore("low", "low"), 1);
    assert.strictEqual(calculateRiskScore("medium", "medium"), 4);
    assert.strictEqual(calculateRiskScore("high", "high"), 9);
    assert.strictEqual(calculateRiskScore("critical", "critical"), 16);
    assert.strictEqual(calculateRiskScore("high", "medium"), 6);
    assert.strictEqual(calculateRiskScore("medium", "critical"), 8);
  });

  it("applies risk resource", () => {
    const provider = new TerraformProvider();
    const result = provider.apply({
      type: "grc_risk",
      name: "data-breach-risk",
      attributes: {
        title: "Data Breach Risk",
        likelihood: "high",
        impact: "critical",
        owner: "security-team",
        mitigationPlan: "Implement encryption at rest and in transit",
        controls: ["CC6.1", "CC6.6"],
      },
    });

    assert.strictEqual(result.success, true);
    assert.strictEqual(
      (result.state.attributes as Record<string, unknown>).score,
      12
    );
  });
});

describe("Agent Policy", () => {
  it("applies agent policy with rules", () => {
    const provider = new TerraformProvider();
    const result = provider.apply({
      type: "grc_agent_policy",
      name: "auto-evidence-collection",
      attributes: {
        name: "Auto Evidence Collection",
        description: "Collects evidence every 6 hours",
        enabled: true,
        schedule: "0 */6 * * *",
        maxRetries: 3,
        timeoutSeconds: 300,
        scope: ["SOC2", "ISO27001"],
        rules: [
          { name: "check-github", condition: "connector == 'github'", action: "collect" },
          { name: "check-aws", condition: "connector == 'aws'", action: "collect" },
        ],
      },
    });

    assert.strictEqual(result.success, true);
    const attrs = result.state.attributes as Record<string, unknown>;
    assert.strictEqual(attrs.enabled, true);
    assert.strictEqual(attrs.maxRetries, 3);
    assert.ok(Array.isArray(attrs.rules));
    assert.strictEqual((attrs.rules as unknown[]).length, 2);
  });
});
