import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { AnomalyDetector } from "./detectors/AnomalyDetector.js";

describe("AnomalyDetector", () => {
  it("should update baseline and detect anomalies", () => {
    const detector = new AnomalyDetector(2.0);
    for (let i = 0; i < 20; i++) detector.updateBaseline("cpu_usage", 50);
    const anomaly = detector.detect("cpu_usage", 100);
    assert.ok(anomaly);
    assert.equal(anomaly.severity, "critical");
  });

  it("should not detect normal values as anomalies", () => {
    const detector = new AnomalyDetector(2.0);
    for (let i = 0; i < 20; i++) detector.updateBaseline("memory", 70);
    const anomaly = detector.detect("memory", 70);
    assert.equal(anomaly, null);
  });

  it("should return baselines", () => {
    const detector = new AnomalyDetector();
    detector.updateBaseline("test", 10);
    assert.equal(detector.getBaselines().length, 1);
  });
});
