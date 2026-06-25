import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { IncidentManager } from "./incidents/IncidentManager.js";

describe("IncidentManager", () => {
  it("should report and manage incident", () => {
    const mgr = new IncidentManager();
    const inc = mgr.reportIncident({ title: "Data breach", type: "data_breach", severity: "critical", description: "Customer data exposed", reportedBy: "SOC", assignee: "IR Team" });
    assert.ok(inc.id);
    assert.equal(inc.status, "detected");

    mgr.transitionIncident(inc.id, "triaged", "IR Lead");
    mgr.transitionIncident(inc.id, "contained", "IR Lead");
    assert.equal(inc.status, "contained");
    assert.equal(inc.timeline.length, 3);
  });

  it("should add evidence with chain of custody", () => {
    const mgr = new IncidentManager();
    const inc = mgr.reportIncident({ title: "Malware", type: "malware", severity: "high", description: "Ransomware detected", reportedBy: "EDR", assignee: "IR" });
    const ev = mgr.addEvidence(inc.id, { type: "forensic_image", name: "disk.img", sha256: "abc123", collectedAt: new Date().toISOString() });
    assert.ok(ev);
    assert.equal(ev.chainOfCustody.length, 1);
  });

  it("should get stats", () => {
    const mgr = new IncidentManager();
    mgr.reportIncident({ title: "A", type: "phishing", severity: "medium", description: "test", reportedBy: "user", assignee: "SOC" });
    mgr.reportIncident({ title: "B", type: "ransomware", severity: "critical", description: "test", reportedBy: "EDR", assignee: "IR" });
    const stats = mgr.getStats();
    assert.equal(stats.total, 2);
  });
});
