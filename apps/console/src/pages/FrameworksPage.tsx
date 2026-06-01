import { useEffect, useState } from 'react';
import { api, ApiError } from '../lib/api';
import { JsonBlock } from '../components/JsonBlock';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';

const FRAMEWORK_BLURBS: Record<string, string> = {
  iso27001: 'Information security management — access, crypto, operations, and supplier controls.',
  nist_csf: 'NIST Cybersecurity Framework — Identify, Protect, Detect, Respond, Recover functions.',
  soc2: 'Trust services criteria for security, availability, and confidentiality attestations.',
  iso42001: 'AI Management System (AIMS) — governance for agentic AI and model supply chain.',
};

export function FrameworksPage() {
  const meta = PAGE_META.frameworks;
  const [packs, setPacks] = useState<unknown[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string>('all');

  useEffect(() => {
    api
      .frameworks()
      .then((r) => setPacks(r.packs))
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Failed to load frameworks'));
  }, []);

  const filtered =
    selected === 'all'
      ? packs
      : packs.filter((p) => (p as { code?: string }).code === selected);

  return (
    <PageShell meta={meta}>
      {error && <p className="error">{error}</p>}

      <div className="card section-gap">
        <div className="form-row">
          <label htmlFor="fw-filter">Filter by framework</label>
          <select id="fw-filter" value={selected} onChange={(e) => setSelected(e.target.value)}>
            <option value="all">All frameworks ({packs.length})</option>
            {packs.map((p) => {
              const code = (p as { code: string }).code;
              return (
                <option key={code} value={code}>
                  {code}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {(filtered as { code: string; name: string; version: string; controls: unknown[] }[]).map(
        (pack) => (
          <div key={pack.code} className="card section-gap">
            <h2>
              {pack.name}{' '}
              <span className="muted-inline">({pack.code})</span>
            </h2>
            <p className="explain-lead">
              Version {pack.version} · {pack.controls.length} controls ·{' '}
              {FRAMEWORK_BLURBS[pack.code] ?? 'Compliance control pack for continuous monitoring.'}
            </p>
            <table>
              <thead>
                <tr>
                  <th>Control ID</th>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Domain</th>
                </tr>
              </thead>
              <tbody>
                {pack.controls.map((c) => {
                  const ctrl = c as {
                    id: string;
                    controlCode: string;
                    title: string;
                    domain?: string;
                  };
                  return (
                    <tr key={ctrl.id}>
                      <td>
                        <code>{ctrl.id}</code>
                      </td>
                      <td>{ctrl.controlCode}</td>
                      <td>{ctrl.title}</td>
                      <td>{ctrl.domain ?? '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      )}

      <div className="card">
        <h2>API response (JSON)</h2>
        <JsonBlock data={packs} />
      </div>
    </PageShell>
  );
}
