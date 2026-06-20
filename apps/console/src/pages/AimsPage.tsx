import { useEffect, useState } from 'react';
import { api, ApiError } from '../lib/api';
import { VENDORS } from '../lib/constants';
import { JsonBlock } from '../components/JsonBlock';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';

const VENDOR_BLURBS: Record<string, string> = {
  anthropic: 'Claude API — constitutional AI, usage policies, and enterprise controls.',
  openai: 'GPT models — API governance, data retention, and enterprise agreements.',
  cursor: 'Cursor IDE agent — Auto Mode, MCP tools, and workspace policy alignment.',
  openclaw: 'OpenClaw gateway — personal assistant pattern extended for GRC operations.',
};

export function AimsPage() {
  const meta = PAGE_META.aims;
  const [tab, setTab] = useState<'gaps' | 'controls'>('gaps');
  const [vendor, setVendor] = useState<string>('');
  const [gapsData, setGapsData] = useState<{ summary: unknown[]; gaps: unknown[] } | null>(null);
  const [controlsData, setControlsData] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (tab !== 'gaps') return;
    setLoading(true);
    setError(null);
    api
      .aimsVendorGaps(vendor || undefined)
      .then(setGapsData)
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Failed'))
      .finally(() => setLoading(false));
  }, [tab, vendor]);

  useEffect(() => {
    if (tab !== 'controls') return;
    setLoading(true);
    setError(null);
    api
      .aimsTechnicalControls()
      .then(setControlsData)
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Failed'))
      .finally(() => setLoading(false));
  }, [tab]);

  return (
    <PageShell meta={meta}>
      <div className="tabs">
        <button type="button" className={tab === 'gaps' ? 'active' : ''} onClick={() => setTab('gaps')}>
          Vendor gap matrix
        </button>
        <button type="button" className={tab === 'controls' ? 'active' : ''} onClick={() => setTab('controls')}>
          Technical controls & clauses
        </button>
      </div>

      {tab === 'gaps' && (
        <div className="card section-gap">
          <div className="form-row">
            <label htmlFor="vendor">Filter by AI vendor</label>
            <select id="vendor" value={vendor} onChange={(e) => setVendor(e.target.value)}>
              <option value="">All vendors — compare supply chain</option>
              {VENDORS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
            {vendor && VENDOR_BLURBS[vendor] && <p className="field-hint">{VENDOR_BLURBS[vendor]}</p>}
          </div>
        </div>
      )}

      {loading && <p className="muted-text">Loading AIMS data…</p>}
      {error && <p className="error">{error}</p>}

      {tab === 'gaps' && gapsData && (
        <>
          <div className="card section-gap">
            <h2>Executive summary</h2>
            <p className="explain-lead">
              Compare critical and high gaps across AI vendors before procurement or deploying agentic
              workflows on A2Z SOC.
            </p>
            <table>
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Total gaps</th>
                  <th>Critical</th>
                  <th>High</th>
                </tr>
              </thead>
              <tbody>
                {(gapsData.summary as Record<string, unknown>[]).map((row) => (
                  <tr key={String(row.vendor)}>
                    <td>{String(row.vendor)}</td>
                    <td>{String(row.totalGaps ?? row.total ?? '—')}</td>
                    <td>{String(row.critical ?? '—')}</td>
                    <td>{String(row.high ?? '—')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card">
            <h2>Gap details {vendor ? `— ${vendor}` : ''}</h2>
            <JsonBlock data={gapsData.gaps} />
          </div>
        </>
      )}

      {tab === 'controls' && controlsData != null && (
        <>
          <div className="card section-gap">
            <h2>AIMS scope template</h2>
            <p className="explain-lead">
              ISO/IEC 42001 scope statement — references production SOC anchor at a2zsoc.com.
            </p>
            <JsonBlock data={(controlsData as { scope: unknown }).scope} />
          </div>
          <div className="grid-2">
            <div className="card">
              <h2>Clause map (4–10)</h2>
              <JsonBlock data={(controlsData as { clauses: unknown[] }).clauses} />
            </div>
            <div className="card">
              <h2>Technical controls (TC-*)</h2>
              <JsonBlock data={(controlsData as { controls: unknown[] }).controls} />
            </div>
          </div>
        </>
      )}
    </PageShell>
  );
}
