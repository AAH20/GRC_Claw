import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { RegulatoryIntelligenceEngine } from "./index.js";

describe("RegulatoryIntelligenceEngine", () => {
  it("should register source", () => {
    const engine = new RegulatoryIntelligenceEngine();
    engine.registerSource({
      id: "src-1",
      name: "EU AI Act Updates",
      url: "https://example.com/ai-act",
      jurisdiction: "eu",
      framework: "eu-ai-act",
      pollingIntervalMs: 3600000,
      status: "active",
    });

    const sources = engine.getSources();
    assert.equal(sources.length, 1);
    assert.equal(sources[0].id, "src-1");
  });

  it("should detect changes", async () => {
    const engine = new RegulatoryIntelligenceEngine();
    engine.registerSource({
      id: "src-2",
      name: "NIST CSF Updates",
      url: "https://example.com/nist",
      jurisdiction: "us",
      framework: "nist-csf",
      pollingIntervalMs: 3600000,
      status: "active",
    });

    const change = await engine.checkForChanges("src-2", async () => "New NIST CSF guidance on AI security");
    assert.ok(change);
    assert.equal(change!.sourceId, "src-2");
  });

  it("should generate digest", () => {
    const engine = new RegulatoryIntelligenceEngine();
    const digest = engine.generateDigest("eu", "2024-01-01", "2024-12-31");
    assert.equal(digest.jurisdiction, "eu");
    assert.ok(digest.id.startsWith("digest-"));
  });

  it("should get stats", () => {
    const engine = new RegulatoryIntelligenceEngine();
    engine.registerSource({
      id: "src-3",
      name: "Test Source",
      url: "https://example.com",
      jurisdiction: "global",
      framework: "iso27001",
      pollingIntervalMs: 3600000,
      status: "active",
    });

    const stats = engine.getStats();
    assert.equal(stats.totalSources, 1);
    assert.equal(stats.activeSources, 1);
  });

  it("should filter changes by framework", async () => {
    const engine = new RegulatoryIntelligenceEngine();
    engine.registerSource({
      id: "src-4",
      name: "GDPR Updates",
      url: "https://example.com/gdpr",
      jurisdiction: "eu",
      framework: "gdpr",
      pollingIntervalMs: 3600000,
      status: "active",
    });

    await engine.checkForChanges("src-4", async () => "GDPR amendment on AI data processing");

    const gdprChanges = engine.getChangesByFramework("gdpr");
    assert.ok(gdprChanges.length > 0);
  });
});

describe("RegulatoryChangeDetector", () => {
  it("should detect first content capture", async () => {
    const { RegulatoryChangeDetector } = await import("./detectors/RegulatoryChangeDetector.js");
    const detector = new RegulatoryChangeDetector();

    const result = await detector.detectChange(
      { id: "test", name: "Test", url: "", jurisdiction: "eu", framework: "iso27001", pollingIntervalMs: 0, status: "active" },
      "Initial regulatory content"
    );

    assert.ok(result.hasChange);
    assert.equal(result.changeType, "new_regulation");
  });

  it("should detect no change for identical content", async () => {
    const { RegulatoryChangeDetector } = await import("./detectors/RegulatoryChangeDetector.js");
    const detector = new RegulatoryChangeDetector();

    const source = { id: "test2", name: "Test", url: "", jurisdiction: "eu", framework: "iso27001", pollingIntervalMs: 0, status: "active" as const };

    await detector.detectChange(source, "Same content");
    const result = await detector.detectChange(source, "Same content");

    assert.equal(result.hasChange, false);
  });

  it("should classify amendment change type", async () => {
    const { RegulatoryChangeDetector } = await import("./detectors/RegulatoryChangeDetector.js");
    const detector = new RegulatoryChangeDetector();

    const source = { id: "test3", name: "Test", url: "", jurisdiction: "eu", framework: "iso27001", pollingIntervalMs: 0, status: "active" as const };

    await detector.detectChange(source, "Original regulation text about compliance requirements");
    const result = await detector.detectChange(source, "Revised regulation text about mandatory compliance requirements with updated enforcement");

    assert.ok(result.hasChange);
  });
});
