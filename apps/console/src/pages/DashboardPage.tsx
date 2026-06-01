import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, ApiError } from '../lib/api';
import { AgentChatWindow } from '../components/AgentChatWindow';
import { JsonBlock } from '../components/JsonBlock';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';
import { loadSettings } from '../lib/settings';

export function DashboardPage() {
  const meta = PAGE_META.dashboard;
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [connectors, setConnectors] = useState<Record<string, unknown> | null>(null);
  const [syncResult, setSyncResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, c] = await Promise.all([api.health(), api.connectors().catch(() => null)]);
      setHealth(h);
      setConnectors(c);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Gateway unreachable — start gateway and check Settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function syncA2z() {
    setSyncing(true);
    setSyncError(null);
    setSyncResult(null);
    try {
      const res = await api.a2zSync();
      setSyncResult(res);
    } catch (e) {
      setSyncError(e instanceof ApiError ? `${e.message}: ${JSON.stringify(e.body)}` : String(e));
    } finally {
      setSyncing(false);
    }
  }

  const settings = loadSettings();
  const a2zMode = health ? String(health.a2z_soc_mode ?? '—') : '—';
  const llmList = (connectors?.llm as { id: string; apiKeyConfigured?: boolean }[]) ?? [];
  const geminiProvider = llmList.find((l) => l.id === 'gemini') ?? llmList[0];
  const geminiAvailable = Boolean(geminiProvider?.apiKeyConfigured);

  return (
    <PageShell
      meta={meta}
      actions={
        <>
          <button type="button" className="primary" onClick={() => void refresh()} disabled={loading}>
            {loading ? 'Refreshing…' : 'Refresh status'}
          </button>
          <Link to="/settings">Gateway settings →</Link>
        </>
      }
    >
      {error && <p className="error">{error}</p>}

      <AgentChatWindow
        llmProviderId={geminiProvider?.id ?? 'gemini'}
        llmAvailable={geminiAvailable || llmList.length > 0}
      />

      {health && (
        <>
          <div className="grid-3 section-gap">
            <div className="stat">
              <div className="label">Gateway service</div>
              <div className="value value-sm">{String(health.service ?? '—')}</div>
            </div>
            <div className="stat">
              <div className="label">A2Z SOC mode</div>
              <div className="value value-sm">{a2zMode}</div>
              <div className="stat-hint">
                {a2zMode === 'private' ? 'Live bridge' : 'Demo — set A2Z_SOC_MODE=private'}
              </div>
            </div>
            <div className="stat">
              <div className="label">Trust tenant</div>
              <div className="value value-sm">{settings.a2zTrustTenantId}</div>
              <div className="stat-hint">
                <a href={`${settings.a2zSocUrl}/trust/${settings.a2zTrustTenantId}`} target="_blank" rel="noreferrer">
                  View on A2Z SOC
                </a>
              </div>
            </div>
            <div className="stat">
              <div className="label">LLM providers</div>
              <div className="value">{String(health.llm_providers ?? 0)}</div>
            </div>
            <div className="stat">
              <div className="label">MCP servers</div>
              <div className="value">{String(health.mcp_servers ?? 0)}</div>
            </div>
            <div className="stat">
              <div className="label">Cloud ingest sources</div>
              <div className="value">
                {Array.isArray(health.cloud_sources) ? health.cloud_sources.length : '—'}
              </div>
            </div>
          </div>

          <div className="card section-gap">
            <h2>Active capabilities</h2>
            <div className="capability-row">
              {health.agentic_ai_security && <span className="badge ok">Agentic AI security</span>}
              {health.iso_42001_aims && <span className="badge ok">ISO 42001 AIMS</span>}
              {health.byoc_connectors && <span className="badge ok">BYOC connectors</span>}
              {health.cloud_security_integration && <span className="badge ok">Cloud security</span>}
            </div>
          </div>

          <div className="grid-2 section-gap">
            <div className="card">
              <h2>Quick navigation</h2>
              <ul className="link-list">
                <li>
                  <Link to="/ingest">Normalize a SIEM or cloud alert</Link> — map to controls
                </li>
                <li>
                  <Link to="/agent">Run a gated agent tool</Link> — read / write / destructive tiers
                </li>
                <li>
                  <Link to="/frameworks">Browse framework packs</Link> — ISO, NIST, SOC 2, AIMS
                </li>
                <li>
                  <Link to="/aims">Review ISO 42001 vendor gaps</Link> — including Cursor
                </li>
                <li>
                  <Link to="/connectors">Configure BYOC LLM / MCP</Link>
                </li>
              </ul>
            </div>
            <div className="card">
              <h2>BYOC summary</h2>
              {connectors ? (
                <JsonBlock data={{ llm: connectors.llm, mcp: connectors.mcp }} />
              ) : (
                <p className="explain-lead">No BYOC connectors loaded — configure env vars on gateway.</p>
              )}
            </div>
          </div>

          <div className="card section-gap a2z-sync-card">
            <h2>A2Z SOC bridge sync</h2>
            <p className="explain-lead">
              Pulls security events from the last hour via Private A2Z SOC. Requires gateway token and{' '}
              <code>A2Z_SOC_MODE=private</code> with <code>A2Z_SOC_BASE_URL</code> configured on the
              gateway host — not a separate page; sync runs here from the control plane.
            </p>
            <div className="actions">
              <button type="button" className="primary" onClick={() => void syncA2z()} disabled={syncing}>
                {syncing ? 'Syncing…' : 'Sync from A2Z SOC'}
              </button>
            </div>
            {syncError && <p className="error">{syncError}</p>}
            {syncResult != null && <JsonBlock data={syncResult} />}
          </div>

          <div className="card">
            <h2>Raw health payload</h2>
            <JsonBlock data={health} />
          </div>
        </>
      )}
    </PageShell>
  );
}
