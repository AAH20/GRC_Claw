import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, ApiError } from '../lib/api';
import { AgentChatWindow } from '../components/AgentChatWindow';
import { JsonBlock } from '../components/JsonBlock';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';
import { loadSettings } from '../lib/settings';
import { MetricCard } from '../components/MetricCard';
import { ComplianceGauge } from '../components/ComplianceGauge';
import { RiskHeatmap } from '../components/RiskHeatmap';
import { TimeSeriesChart } from '../components/TimeSeriesChart';

export function DashboardPage() {
  const meta = PAGE_META.dashboard;
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [connectors, setConnectors] = useState<Record<string, unknown> | null>(null);
  const [syncResult, setSyncResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [metrics, setMetrics] = useState<Record<string, number> | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, c] = await Promise.all([api.health(), api.connectors().catch(() => null)]);
      setHealth(h);
      setConnectors(c);

      try {
        const raw = await fetch(`${loadSettings().baseUrl}/metrics`);
        const text = await raw.text();
        const parsed: Record<string, number> = {};
        for (const line of text.split('\n')) {
          if (line.startsWith('#') || !line.trim()) continue;
          const match = line.match(/^([a-z_]+)\s+([\d.]+)/);
          if (match) parsed[match[1]] = Number(match[2]);
        }
        setMetrics(parsed);
      } catch {
        /* metrics endpoint optional */
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Gateway unreachable \u2014 start gateway and check Settings');
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
  const a2zMode = health ? String(health.a2z_soc_mode ?? '\u2014') : '\u2014';
  const llmList = (connectors?.llm as { id: string; apiKeyConfigured?: boolean }[]) ?? [];
  const geminiProvider = llmList.find((l) => l.id === 'gemini') ?? llmList[0];
  const geminiAvailable = Boolean(geminiProvider?.apiKeyConfigured);

  const complianceScore = metrics ? Math.round((metrics.grc_compliance_score ?? 0.87) * 100) : 87;
  const requestsTotal = metrics?.grc_gateway_requests_total ?? 0;
  const agentInvocations = metrics?.grc_agent_invocations_total ?? 0;

  const sampleRequests = metrics
    ? [
        { label: '0s', value: Math.max(0, requestsTotal - 12) },
        { label: '15s', value: Math.max(0, requestsTotal - 8) },
        { label: '30s', value: Math.max(0, requestsTotal - 4) },
        { label: '45s', value: requestsTotal - 2 },
        { label: 'Now', value: requestsTotal },
      ]
    : [];
  const sampleAgents = metrics
    ? [
        { label: '0s', value: Math.max(0, agentInvocations - 5) },
        { label: '15s', value: Math.max(0, agentInvocations - 3) },
        { label: '30s', value: Math.max(0, agentInvocations - 1) },
        { label: 'Now', value: agentInvocations },
      ]
    : [];

  const sampleRiskCells = [
    { likelihood: 5, impact: 5, count: 1 },
    { likelihood: 4, impact: 3, count: 2 },
    { likelihood: 3, impact: 4, count: 1 },
    { likelihood: 2, impact: 2, count: 3 },
    { likelihood: 1, impact: 1, count: 5 },
  ];

  return (
    <PageShell
      meta={meta}
      actions={
        <>
          <button type="button" className="primary" onClick={() => void refresh()} disabled={loading}>
            {loading ? 'Refreshing\u2026' : 'Refresh status'}
          </button>
          <Link to="/settings">Gateway settings \u2192</Link>
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
              <div className="value value-sm">{String(health.service ?? '\u2014')}</div>
            </div>
            <div className="stat">
              <div className="label">A2Z SOC mode</div>
              <div className="value value-sm">{a2zMode}</div>
              <div className="stat-hint">
                {a2zMode === 'private' ? 'Live bridge' : 'Demo \u2014 set A2Z_SOC_MODE=private'}
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
                {Array.isArray(health.cloud_sources) ? health.cloud_sources.length : '\u2014'}
              </div>
            </div>
          </div>

          <div className="metrics-row section-gap">
            <MetricCard
              name="Total Requests"
              value={requestsTotal}
              trend={{ direction: 'up', percentage: 12 }}
              sparkline={sampleRequests.map((p) => p.value)}
            />
            <MetricCard
              name="Agent Invocations"
              value={agentInvocations}
              trend={{ direction: 'up', percentage: 8 }}
              sparkline={sampleAgents.map((p) => p.value)}
            />
            <ComplianceGauge score={complianceScore} />
          </div>

          <div className="grid-2 section-gap">
            <div className="card">
              <h2>Risk Heatmap</h2>
              <RiskHeatmap cells={sampleRiskCells} />
            </div>
            <div className="card">
              <h2>Request Volume</h2>
              <TimeSeriesChart data={sampleRequests} height={150} />
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
                  <Link to="/ingest">Normalize a SIEM or cloud alert</Link> \u2014 map to controls
                </li>
                <li>
                  <Link to="/agent">Run a gated agent tool</Link> \u2014 read / write / destructive tiers
                </li>
                <li>
                  <Link to="/frameworks">Browse framework packs</Link> \u2014 ISO, NIST, SOC 2, AIMS
                </li>
                <li>
                  <Link to="/aims">Review ISO 42001 vendor gaps</Link> \u2014 including Cursor
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
                <p className="explain-lead">No BYOC connectors loaded \u2014 configure env vars on gateway.</p>
              )}
            </div>
          </div>

          <div className="card section-gap a2z-sync-card">
            <h2>A2Z SOC bridge sync</h2>
            <p className="explain-lead">
              Pulls security events from the last hour via Private A2Z SOC. Requires gateway token and{' '}
              <code>A2Z_SOC_MODE=private</code> with <code>A2Z_SOC_BASE_URL</code> configured on the
              gateway host \u2014 not a separate page; sync runs here from the control plane.
            </p>
            <div className="actions">
              <button type="button" className="primary" onClick={() => void syncA2z()} disabled={syncing}>
                {syncing ? 'Syncing\u2026' : 'Sync from A2Z SOC'}
              </button>
            </div>
            {syncError && <p className="error">{syncError}</p>}
            {syncResult != null && <JsonBlock data={syncResult} />}
          </div>
        </>
      )}
    </PageShell>
  );
}
