import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../lib/api';
import { JsonBlock } from '../components/JsonBlock';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';

type LlmRow = { id: string; label?: string; kind?: string; defaultModel?: string };
type McpRow = { id: string; transport?: string; url?: string };

export function ConnectorsPage() {
  const meta = PAGE_META.connectors;
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [llmId, setLlmId] = useState('');
  const [chatBody, setChatBody] = useState(
    JSON.stringify(
      { messages: [{ role: 'user', content: 'Summarize our GRC posture in one sentence.' }] },
      null,
      2
    )
  );
  const [chatResult, setChatResult] = useState<unknown>(null);

  const [mcpId, setMcpId] = useState('');
  const [mcpTools, setMcpTools] = useState<unknown[] | null>(null);
  const [mcpCallBody, setMcpCallBody] = useState(
    JSON.stringify({ name: 'tool_name', arguments: {} }, null, 2)
  );
  const [mcpCallResult, setMcpCallResult] = useState<unknown>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const c = await api.connectors();
      setData(c);
      const llms = (c.llm as LlmRow[]) ?? [];
      const mcps = (c.mcp as McpRow[]) ?? [];
      setLlmId((prev) => prev || (llms[0]?.id ?? ''));
      setMcpId((prev) => prev || (mcps[0]?.id ?? ''));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load connectors');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function reload() {
    setMsg(null);
    setError(null);
    try {
      await api.connectorsReload();
      setMsg('Connectors reloaded from gateway environment.');
      await refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Reload failed');
    }
  }

  async function sendChat() {
    setChatResult(null);
    setError(null);
    try {
      const body = JSON.parse(chatBody) as unknown;
      const res = await api.llmChat(llmId, body);
      setChatResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? `${e.message}: ${JSON.stringify(e.body)}` : String(e));
    }
  }

  async function fetchMcpTools() {
    setMcpTools(null);
    setError(null);
    try {
      const res = await api.mcpTools(mcpId);
      setMcpTools(res.tools);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to list MCP tools');
    }
  }

  async function callMcp() {
    setMcpCallResult(null);
    setError(null);
    try {
      const body = JSON.parse(mcpCallBody) as unknown;
      const res = await api.mcpCall(mcpId, body);
      setMcpCallResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? `${e.message}: ${JSON.stringify(e.body)}` : String(e));
    }
  }

  const llms = (data?.llm as LlmRow[]) ?? [];
  const mcps = (data?.mcp as McpRow[]) ?? [];

  return (
    <PageShell
      meta={meta}
      actions={
        <>
          <button type="button" className="primary" onClick={() => void refresh()} disabled={loading}>
            Refresh registry
          </button>
          <button type="button" onClick={() => void reload()}>
            Reload from env
          </button>
        </>
      }
    >
      {msg && <p className="success-msg">{msg}</p>}
      {error && <p className="error">{error}</p>}

      <div className="grid-2 section-gap">
        <div className="card">
          <h2>LLM providers ({llms.length})</h2>
          <p className="explain-lead">
            Configure via <code>GRC_CLAW_CONNECTORS_CONFIG</code> or{' '}
            <code>GRC_CLAW_CONNECTORS_JSON</code> on the gateway.
          </p>
          {llms.length === 0 ? (
            <p className="muted-text">No LLM providers registered.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Label</th>
                  <th>Kind</th>
                  <th>Default model</th>
                </tr>
              </thead>
              <tbody>
                {llms.map((l) => (
                  <tr key={l.id}>
                    <td>
                      <code>{l.id}</code>
                    </td>
                    <td>{l.label ?? '—'}</td>
                    <td>{l.kind ?? '—'}</td>
                    <td>{l.defaultModel ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div className="card">
          <h2>MCP servers ({mcps.length})</h2>
          <p className="explain-lead">
            Cursor Auto Mode can use MCP tools listed here — each call still passes through exec
            policy when invoked via the agent runtime.
          </p>
          {mcps.length === 0 ? (
            <p className="muted-text">No MCP servers registered.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Transport</th>
                </tr>
              </thead>
              <tbody>
                {mcps.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <code>{m.id}</code>
                    </td>
                    <td>{m.transport ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="card section-gap">
        <h2>Test LLM chat</h2>
        <div className="form-row">
          <label htmlFor="llm-id">Provider ID</label>
          <select id="llm-id" value={llmId} onChange={(e) => setLlmId(e.target.value)}>
            {llms.map((l) => (
              <option key={l.id} value={l.id}>
                {l.id}
              </option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="chat-body">Request body</label>
          <textarea id="chat-body" value={chatBody} onChange={(e) => setChatBody(e.target.value)} />
        </div>
        <div className="actions">
          <button type="button" className="primary" onClick={() => void sendChat()} disabled={!llmId}>
            Send chat
          </button>
        </div>
        {chatResult != null && <JsonBlock data={chatResult} />}
      </div>

      <div className="card section-gap">
        <h2>MCP tools & invoke</h2>
        <div className="form-row">
          <label htmlFor="mcp-id">Server ID</label>
          <select id="mcp-id" value={mcpId} onChange={(e) => setMcpId(e.target.value)}>
            {mcps.map((m) => (
              <option key={m.id} value={m.id}>
                {m.id}
              </option>
            ))}
          </select>
        </div>
        <div className="actions">
          <button type="button" onClick={() => void fetchMcpTools()} disabled={!mcpId}>
            List tools
          </button>
        </div>
        {mcpTools != null && (
          <>
            <h3 className="result-heading">Discovered tools</h3>
            <JsonBlock data={mcpTools} />
          </>
        )}
        <div className="form-row">
          <label htmlFor="mcp-call">Tool call body</label>
          <textarea id="mcp-call" value={mcpCallBody} onChange={(e) => setMcpCallBody(e.target.value)} />
        </div>
        <div className="actions">
          <button type="button" className="primary" onClick={() => void callMcp()} disabled={!mcpId}>
            Invoke MCP tool
          </button>
        </div>
        {mcpCallResult != null && <JsonBlock data={mcpCallResult} />}
      </div>

      {data && (
        <div className="card">
          <h2>Full registry JSON</h2>
          <JsonBlock data={data} />
        </div>
      )}
    </PageShell>
  );
}
