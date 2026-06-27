import { useCallback, useEffect, useRef, useState } from 'react';
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

interface SocEvent {
  id: string;
  timestamp: string;
  severity: string;
  source: string;
  title: string;
  control?: string;
}

interface ComplianceUpdate {
  overall_score: number;
  control?: string;
  previous_score?: number;
  delta?: number;
  timestamp: string;
}

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
  const [riskCells, setRiskCells] = useState<{ likelihood: number; impact: number; count: number }[]>([]);
  const [liveScore, setLiveScore] = useState<number | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [socEvents, setSocEvents] = useState<SocEvent[]>([]);
  const [complianceUpdates, setComplianceUpdates] = useState<ComplianceUpdate[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // WebSocket connection for real-time compliance + SOC events
  useEffect(() => {
    const settings = loadSettings();
    if (!settings.baseUrl || !settings.token) return;

    const wsUrl = settings.baseUrl.replace(/^http/, 'ws');
    let socket: WebSocket | null = null;
    const MAX_RECONNECT_DELAY = 30_000;

    function connect() {
      try {
        setWsStatus('connecting');
        socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          reconnectAttemptsRef.current = 0;
          socket?.send(JSON.stringify({
            type: 'connect',
            params: { auth: { token: settings.token }, role: 'operator' },
          }));
        };

        socket.onmessage = (event) => {
          try {
            const frame = JSON.parse(String(event.data));
            if (frame.type === 'hello-ok') {
              socket?.send(JSON.stringify({
                type: 'subscribe',
                channel: 'compliance_updates',
                token: settings.token,
              }));
              socket?.send(JSON.stringify({
                type: 'subscribe',
                channel: 'soc_events',
                token: settings.token,
              }));
              return;
            }
            if (frame.type === 'subscribed') {
              if (frame.channel === 'compliance_updates' || frame.channel === 'soc_events') {
                setWsConnected(true);
                setWsStatus('connected');
              }
              return;
            }
            if (frame.type === 'compliance_update' && frame.data) {
              const data = frame.data as ComplianceUpdate;
              if (typeof data.overall_score === 'number') {
                setLiveScore(Math.round(data.overall_score));
              }
              setComplianceUpdates((prev) => {
                const next = [{ ...data, timestamp: data.timestamp ?? new Date().toISOString() }, ...prev];
                return next.slice(0, 20);
              });
              return;
            }
            if (frame.type === 'soc_event' && frame.data) {
              const evt = frame.data as SocEvent;
              setSocEvents((prev) => {
                const next = [{ ...evt, timestamp: evt.timestamp ?? new Date().toISOString() }, ...prev];
                return next.slice(0, 30);
              });
            }
          } catch { /* ignore malformed frames */ }
        };

        socket.onclose = () => {
          setWsConnected(false);
          wsRef.current = null;
          const delay = Math.min(
            5000 * Math.pow(2, reconnectAttemptsRef.current),
            MAX_RECONNECT_DELAY,
          );
          reconnectAttemptsRef.current += 1;
          reconnectTimerRef.current = setTimeout(connect, delay);
        };

        socket.onerror = () => {
          setWsStatus('error');
          socket?.close();
        };
      } catch {
        setWsStatus('error');
      }
    }

    connect();

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
      wsRef.current = null;
      setWsConnected(false);
      setWsStatus('disconnected');
    };
  }, []);

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

      try {
        const heatmap = await api.riskHeatmap();
        setRiskCells(
          heatmap.cells.map((c) => ({
            likelihood: c.likelihood,
            impact: c.impact,
            count: c.scenarios.length,
          })),
        );
      } catch {
        /* risk heatmap endpoint optional */
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

  const complianceScore = liveScore ?? (metrics ? Math.round((metrics.grc_compliance_score ?? 0.87) * 100) : 87);
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
            {wsConnected && (
              <div className="live-indicator" style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '0.85rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)', display: 'inline-block', animation: 'pulse 2s infinite' }} />
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>Live</span>
              </div>
            )}
            {!wsConnected && wsStatus === 'connecting' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '0.85rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>Connecting\u2026</span>
              </div>
            )}
            {wsStatus === 'error' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '0.85rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />
                <span style={{ color: '#ef4444', fontWeight: 600 }}>Disconnected</span>
              </div>
            )}
          </div>

          <div className="grid-2 section-gap">
            <div className="card">
              <h2>Risk Heatmap</h2>
              <RiskHeatmap cells={riskCells} />
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

          {socEvents.length > 0 && (
            <div className="card section-gap">
              <h2>Live SOC Events</h2>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border, #333)', textAlign: 'left' }}>
                      <th style={{ padding: '6px 8px' }}>Time</th>
                      <th style={{ padding: '6px 8px' }}>Severity</th>
                      <th style={{ padding: '6px 8px' }}>Source</th>
                      <th style={{ padding: '6px 8px' }}>Event</th>
                      <th style={{ padding: '6px 8px' }}>Control</th>
                    </tr>
                  </thead>
                  <tbody>
                    {socEvents.map((evt) => (
                      <tr key={evt.id} style={{ borderBottom: '1px solid var(--border, #222)' }}>
                        <td style={{ padding: '6px 8px', color: '#999' }}>
                          {new Date(evt.timestamp).toLocaleTimeString()}
                        </td>
                        <td style={{ padding: '6px 8px' }}>
                          <span style={{
                            padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600,
                            background: evt.severity === 'critical' ? '#7f1d1d' : evt.severity === 'high' ? '#78350f' : evt.severity === 'medium' ? '#1e3a5f' : '#1a3a1a',
                            color: evt.severity === 'critical' ? '#fca5a5' : evt.severity === 'high' ? '#fcd34d' : evt.severity === 'medium' ? '#93c5fd' : '#86efac',
                          }}>
                            {evt.severity.toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '6px 8px', color: '#999' }}>{evt.source}</td>
                        <td style={{ padding: '6px 8px' }}>{evt.title}</td>
                        <td style={{ padding: '6px 8px', color: '#999' }}>{evt.control ?? '\u2014'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {complianceUpdates.length > 0 && (
            <div className="card section-gap">
              <h2>Real-time Compliance Updates</h2>
              <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                {complianceUpdates.map((update, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 0', borderBottom: '1px solid var(--border, #222)' }}>
                    <span style={{ fontSize: '0.75rem', color: '#999', minWidth: '70px' }}>
                      {new Date(update.timestamp).toLocaleTimeString()}
                    </span>
                    <span style={{ fontWeight: 600, minWidth: '40px' }}>
                      {update.overall_score}/100
                    </span>
                    {typeof update.delta === 'number' && update.delta !== 0 && (
                      <span style={{ color: update.delta > 0 ? '#22c55e' : '#ef4444', fontSize: '0.85rem' }}>
                        {update.delta > 0 ? '+' : ''}{update.delta}
                      </span>
                    )}
                    {update.control && (
                      <span style={{ color: '#999', fontSize: '0.85rem' }}>{update.control}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
