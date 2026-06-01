import { useState } from 'react';
import { loadSettings, saveSettings, type ConsoleSettings } from '../lib/settings';
import { api, ApiError } from '../lib/api';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';
import { CopyBlock } from '../components/CursorAutoPanel';
import { buildCurl, CURSOR_AUTO_RULES, CURSOR_MCP_SNIPPET } from '../lib/cursorAuto';

export function SettingsPage() {
  const meta = PAGE_META.settings;
  const [form, setForm] = useState<ConsoleSettings>(() => loadSettings());
  const [saved, setSaved] = useState(false);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<string>('idle');

  function update<K extends keyof ConsoleSettings>(key: K, value: ConsoleSettings[K]) {
    setForm((f) => ({ ...f, [key]: value }));
    setSaved(false);
  }

  function persist() {
    saveSettings(form);
    setSaved(true);
    window.location.reload();
  }

  async function testHealth() {
    setHealthOk(null);
    setHealthError(null);
    saveSettings(form);
    try {
      await api.health();
      setHealthOk(true);
    } catch (e) {
      setHealthOk(false);
      setHealthError(e instanceof ApiError ? e.message : 'Unreachable');
    }
  }

  function testWebSocket() {
    setWsStatus('connecting');
    const base =
      form.baseUrl.trim() ||
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
    const wsUrl = base.replace(/^http/, 'ws').replace(/\/$/, '');
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          type: 'connect',
          params: { auth: { token: form.token }, role: 'operator' },
        })
      );
    };
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(String(ev.data)) as { type?: string };
        if (msg.type === 'hello-ok') {
          setWsStatus('hello-ok — gateway WebSocket authenticated');
          ws.close();
        }
      } catch {
        setWsStatus('invalid_frame');
        ws.close();
      }
    };
    ws.onerror = () => setWsStatus('error');
    ws.onclose = (ev) => {
      setWsStatus((prev) => (prev === 'connecting' ? `closed (${ev.code})` : prev));
    };
  }

  return (
    <PageShell meta={meta}>
      <div className="card section-gap">
        <h2>Gateway connection</h2>
        <div className="form-row">
          <label htmlFor="baseUrl">Gateway base URL</label>
          <input
            id="baseUrl"
            value={form.baseUrl}
            onChange={(e) => update('baseUrl', e.target.value)}
            placeholder="Empty = Vite proxy (dev) or same origin (prod)"
          />
          <p className="field-hint">Dev default proxies to http://127.0.0.1:18791 via Vite.</p>
        </div>
        <div className="form-row">
          <label htmlFor="token">X-GRC-Claw-Token</label>
          <input
            id="token"
            type="password"
            value={form.token}
            onChange={(e) => update('token', e.target.value)}
            placeholder="Must match GRC_CLAW_GATEWAY_TOKEN on gateway host"
          />
        </div>
        <div className="form-row">
          <label htmlFor="tenantId">Default tenant ID (ingest & agent)</label>
          <input
            id="tenantId"
            type="number"
            min={1}
            value={form.tenantId}
            onChange={(e) => update('tenantId', Number(e.target.value) || 1)}
          />
        </div>
        <div className="actions">
          <button type="button" className="primary" onClick={persist}>
            Save & reload
          </button>
          <button type="button" onClick={() => void testHealth()}>
            Test /health
          </button>
          <button type="button" onClick={testWebSocket} disabled={!form.token}>
            Test WebSocket
          </button>
        </div>
        {saved && <p className="success-msg">Settings saved.</p>}
        {healthOk === true && <p className="success-msg">Gateway reachable.</p>}
        {healthOk === false && <p className="error">Health check failed: {healthError}</p>}
        {wsStatus !== 'idle' && <p className="field-hint">WebSocket: {wsStatus}</p>}
      </div>

      <div className="card section-gap">
        <h2>A2Z SOC trust badge</h2>
        <p className="explain-lead">
          The badge on every page links to your public trust profile on A2Z SOC — continuous
          compliance posture for customers and auditors.
        </p>
        <div className="grid-2">
          <div className="form-row">
            <label htmlFor="a2zSocUrl">A2Z SOC base URL</label>
            <input
              id="a2zSocUrl"
              value={form.a2zSocUrl}
              onChange={(e) => update('a2zSocUrl', e.target.value)}
            />
          </div>
          <div className="form-row">
            <label htmlFor="a2zTrustTenantId">Trust profile tenant ID</label>
            <input
              id="a2zTrustTenantId"
              value={form.a2zTrustTenantId}
              onChange={(e) => update('a2zTrustTenantId', e.target.value)}
            />
          </div>
          <div className="form-row">
            <label htmlFor="trustTier">Badge tier label</label>
            <input id="trustTier" value={form.trustTier} onChange={(e) => update('trustTier', e.target.value)} />
          </div>
          <div className="form-row">
            <label htmlFor="trustScore">Trust score (0–100)</label>
            <input
              id="trustScore"
              type="number"
              min={0}
              max={100}
              value={form.trustScore}
              onChange={(e) => update('trustScore', Number(e.target.value) || 0)}
            />
          </div>
        </div>
      </div>

      <div className="card section-gap">
        <h2>Cursor Auto Mode</h2>
        <p className="explain-lead">
          When enabled, each page shows API snippets, curl commands, and agent instructions so Cursor
          Agent and Automations can call the gateway safely — read-tier tools first, destructive only
          with approval.
        </p>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.cursorAutoMode}
            onChange={(e) => update('cursorAutoMode', e.target.checked)}
          />
          Show Cursor Auto Mode panels on every page
        </label>
        <CopyBlock text={CURSOR_MCP_SNIPPET} label="Suggested MCP / gateway config" />
        <CopyBlock text={CURSOR_AUTO_RULES} label="Agent rules (paste into Cursor rules or automation prompt)" />
        <CopyBlock text={buildCurl(meta.cursor)} label="Health check curl" />
        <p className="field-hint">
          Machine-readable API map:{' '}
          <a href="/llms.txt" target="_blank" rel="noreferrer">
            /llms.txt
          </a>
        </p>
      </div>

      <div className="card">
        <h2>Dev quick start</h2>
        <pre className="json-block quick-start">{`cd GRC_Claw
npm install && npm run build
GRC_CLAW_GATEWAY_TOKEN=grc-test-token npm run gateway
npm run console   # http://localhost:5174`}</pre>
      </div>
    </PageShell>
  );
}
