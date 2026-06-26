import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { FrameworkCrosswalk } from './FrameworkCrosswalk.js';
import {
  SOC2_ISO27001_MAPPINGS,
  NISTCSF_ISO27001_MAPPINGS,
  SOC2_NISTCSF_MAPPINGS,
  FEDRAMP_NIST80053_MAPPINGS,
  CMMC_NIST800171_MAPPINGS,
} from './mappings/index.js';

describe('FrameworkCrosswalk', () => {
  const crosswalk = new FrameworkCrosswalk();

  describe('getMappings', () => {
    it('returns SOC2 to ISO 27001 mappings', () => {
      const mappings = crosswalk.getMappings('soc2', 'iso27001');
      assert.ok(mappings.length > 0);
      assert.equal(mappings[0].sourceFramework, 'soc2');
      assert.equal(mappings[0].targetFramework, 'iso27001');
    });

    it('is symmetric - order does not matter', () => {
      const ab = crosswalk.getMappings('soc2', 'iso27001');
      const ba = crosswalk.getMappings('iso27001', 'soc2');
      assert.equal(ab.length, ba.length);
    });

    it('handles framework name variations', () => {
      const m1 = crosswalk.getMappings('SOC 2', 'ISO 27001');
      const m2 = crosswalk.getMappings('soc2', 'iso27001');
      assert.equal(m1.length, m2.length);
    });

    it('returns empty array for unsupported pair', () => {
      const mappings = crosswalk.getMappings('unknown_fw', 'another_fw');
      assert.equal(mappings.length, 0);
    });

    it('returns NIST CSF to ISO 27001 mappings', () => {
      const mappings = crosswalk.getMappings('nist_csf', 'iso27001');
      assert.ok(mappings.length > 0);
    });

    it('returns FedRAMP to NIST 800-53 mappings', () => {
      const mappings = crosswalk.getMappings('fedramp', 'nist_800_53');
      assert.ok(mappings.length > 0);
    });
  });

  describe('addMapping', () => {
    it('adds a custom mapping', () => {
      const cw = new FrameworkCrosswalk();
      cw.addMapping({
        sourceFramework: 'custom_a',
        sourceControl: 'CTRL-1',
        targetFramework: 'custom_b',
        targetControl: 'CTRL-10',
        confidence: 0.9,
        relationship: 'equivalent',
      });
      const mappings = cw.getMappings('custom_a', 'custom_b');
      assert.equal(mappings.length, 1);
      assert.equal(mappings[0].sourceControl, 'CTRL-1');
    });
  });

  describe('getSupportedPairs', () => {
    it('returns a non-empty list of supported pairs', () => {
      const pairs = crosswalk.getSupportedPairs();
      assert.ok(pairs.length >= 10);
    });

    it('includes soc2-iso27001 pair', () => {
      const pairs = crosswalk.getSupportedPairs();
      const hasPair = pairs.some(
        ([a, b]) =>
          (a === 'soc2' && b === 'iso27001') ||
          (a === 'iso27001' && b === 'soc2'),
      );
      assert.ok(hasPair);
    });
  });

  describe('generateCrosswalk', () => {
    it('generates a full crosswalk report', () => {
      const report = crosswalk.generateCrosswalk('soc2', 'iso27001');
      assert.equal(report.sourceFramework, 'soc2');
      assert.equal(report.targetFramework, 'iso27001');
      assert.ok(report.mappings.length > 0);
      assert.ok(report.coverage >= 0 && report.coverage <= 1);
      assert.ok(Array.isArray(report.gaps));
    });

    it('reports gaps for low-confidence mappings', () => {
      const report = crosswalk.generateCrosswalk('soc2', 'iso27001');
      assert.ok(typeof report.coverage === 'number');
    });

    it('returns zero coverage for unknown pair', () => {
      const report = crosswalk.generateCrosswalk('unknown_a', 'unknown_b');
      assert.equal(report.mappings.length, 0);
      assert.equal(report.coverage, 0);
      assert.ok(report.gaps.length > 0);
    });
  });

  describe('findOverlaps', () => {
    it('calculates overlap between SOC2 and ISO 27001', () => {
      const overlap = crosswalk.findOverlaps('soc2', 'iso27001');
      assert.equal(overlap.framework1, 'soc2');
      assert.equal(overlap.framework2, 'iso27001');
      assert.ok(overlap.overlappingControls >= 0);
      assert.ok(overlap.totalControls > 0);
      assert.ok(overlap.overlapPercentage >= 0);
    });

    it('handles symmetric framework order', () => {
      const a = crosswalk.findOverlaps('soc2', 'iso27001');
      const b = crosswalk.findOverlaps('iso27001', 'soc2');
      assert.equal(a.framework1, 'soc2');
      assert.equal(b.framework1, 'iso27001');
    });
  });

  describe('findEquivalentControls', () => {
    it('finds equivalent controls by source control ID', () => {
      const results = crosswalk.findEquivalentControls('CC6.1');
      assert.ok(results.length > 0);
      assert.ok(results.some((m) => m.sourceControl === 'CC6.1'));
    });

    it('finds equivalent controls by target control ID', () => {
      const results = crosswalk.findEquivalentControls('A.8.5');
      assert.ok(results.length > 0);
      assert.ok(results.some((m) => m.targetControl === 'A.8.5'));
    });

    it('returns empty for unknown control', () => {
      const results = crosswalk.findEquivalentControls('NONEXISTENT-999');
      assert.equal(results.length, 0);
    });

    it('results are sorted by confidence descending', () => {
      const results = crosswalk.findEquivalentControls('CC6.1');
      for (let i = 1; i < results.length; i++) {
        assert.ok(results[i - 1].confidence >= results[i].confidence);
      }
    });
  });

  describe('calculateMultiFrameworkCoverage', () => {
    it('returns coverage for control IDs across frameworks', () => {
      const coverage = crosswalk.calculateMultiFrameworkCoverage(
        ['CC6.1', 'CC7.2', 'A.8.5'],
        ['soc2', 'iso27001'],
      );
      assert.ok(coverage >= 0 && coverage <= 1);
    });

    it('returns 0 for empty inputs', () => {
      assert.equal(crosswalk.calculateMultiFrameworkCoverage([], ['soc2']), 0);
      assert.equal(
        crosswalk.calculateMultiFrameworkCoverage(['CC6.1'], []),
        0,
      );
    });

    it('increases with more matching controls', () => {
      const low = crosswalk.calculateMultiFrameworkCoverage(
        ['CC6.1'],
        ['soc2', 'iso27001'],
      );
      const high = crosswalk.calculateMultiFrameworkCoverage(
        ['CC6.1', 'CC6.2', 'CC6.3', 'CC7.1', 'CC7.2'],
        ['soc2', 'iso27001'],
      );
      assert.ok(high >= low);
    });
  });

  describe('Mapping data integrity', () => {
    it('SOC2-ISO27001 mappings have valid structure', () => {
      for (const m of SOC2_ISO27001_MAPPINGS) {
        assert.equal(m.sourceFramework, 'soc2');
        assert.equal(m.targetFramework, 'iso27001');
        assert.ok(m.confidence >= 0 && m.confidence <= 1);
        assert.ok(['equivalent', 'partial', 'supports'].includes(m.relationship));
        assert.ok(m.sourceControl.length > 0);
        assert.ok(m.targetControl.length > 0);
      }
    });

    it('all mapping arrays are non-empty', () => {
      assert.ok(SOC2_ISO27001_MAPPINGS.length > 0);
      assert.ok(NISTCSF_ISO27001_MAPPINGS.length > 0);
      assert.ok(SOC2_NISTCSF_MAPPINGS.length > 0);
      assert.ok(FEDRAMP_NIST80053_MAPPINGS.length > 0);
      assert.ok(CMMC_NIST800171_MAPPINGS.length > 0);
    });

    it('FedRAMP-NIST 800-53 mappings all have confidence 1.0', () => {
      for (const m of FEDRAMP_NIST80053_MAPPINGS) {
        assert.equal(m.confidence, 1.0);
        assert.equal(m.relationship, 'equivalent');
      }
    });

    it('CMMC-NIST 800-171 mappings all have confidence 1.0', () => {
      for (const m of CMMC_NIST800171_MAPPINGS) {
        assert.equal(m.confidence, 1.0);
        assert.equal(m.relationship, 'equivalent');
      }
    });
  });

  describe('listAllMappings', () => {
    it('returns all built-in mappings', () => {
      const all = crosswalk.listAllMappings();
      assert.ok(all.length > 100);
    });
  });
});
