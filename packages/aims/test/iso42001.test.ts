import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  AIMS_SCOPE_TEMPLATE,
  listClauseMap,
  listTechnicalControls,
  listVendorGaps,
  listVendorGapSummary,
  VENDOR_GAP_MATRIX,
} from '@grc-claw/aims';

describe('ISO/IEC 42001 AIMS (@grc-claw/aims)', () => {
  it('vendor gap matrix covers Anthropic, OpenAI, Cursor, OpenClaw', () => {
    const vendors = new Set(VENDOR_GAP_MATRIX.map((r) => r.vendor));
    assert.equal(vendors.size, 4);
    for (const v of ['anthropic', 'openai', 'cursor', 'openclaw'] as const) {
      assert.ok(vendors.has(v), `missing vendor ${v}`);
    }
    assert.ok(VENDOR_GAP_MATRIX.length >= 8);
  });

  it('listVendorGaps filters by vendor', () => {
    const anthropic = listVendorGaps('anthropic');
    assert.ok(anthropic.every((r) => r.vendor === 'anthropic'));
    assert.ok(anthropic.length >= 2);
  });

  it('vendor gap summary has four vendors', () => {
    const summary = listVendorGapSummary();
    assert.equal(summary.length, 4);
  });

  it('technical controls map to GRC_Claw components', () => {
    const controls = listTechnicalControls();
    assert.equal(controls.length, 6);
    assert.ok(controls.some((c) => c.grcClawComponent.includes('agent-runtime')));
    assert.ok(controls.some((c) => c.grcClawComponent.includes('gateway')));
  });

  it('clause map covers clauses 4–10', () => {
    const clauses = listClauseMap();
    assert.equal(clauses.length, 7);
    assert.deepEqual(
      clauses.map((c) => c.clause),
      ['4', '5', '6', '7', '8', '9', '10']
    );
  });

  it('AIMS scope references a2z-soc.com', () => {
    assert.equal(AIMS_SCOPE_TEMPLATE.standard, 'ISO/IEC 42001:2023');
    assert.match(AIMS_SCOPE_TEMPLATE.productionSoc, /a2z-soc\.com/);
  });
});
