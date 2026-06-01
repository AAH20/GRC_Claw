import { useState } from 'react';
import { api, ApiError } from '../lib/api';
import { BUILTIN_TOOLS } from '../lib/constants';
import { JsonBlock } from '../components/JsonBlock';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';

const DEFAULT_ARGS: Record<string, string> = {
  'grc.list_controls': JSON.stringify({ tenantId: 1 }, null, 2),
  'grc.get_compliance_score': JSON.stringify({ tenantId: 1 }, null, 2),
  'evidence.read': JSON.stringify({ evidenceId: 'sample' }, null, 2),
  'soc.query_events': JSON.stringify({ tenantId: 1, limit: 10 }, null, 2),
  'soar.run_playbook': JSON.stringify({ playbookId: 'demo', tenantId: 1 }, null, 2),
};

const TIER_HELP: Record<string, string> = {
  read: 'Auto-allowed — safe for Cursor Auto Mode and routine automation.',
  write: 'Requires idempotencyKey — prevents duplicate evidence or control updates.',
  destructive: 'Requires approvalToken — SOAR playbooks and firewall changes need human gate.',
};

export function AgentPage() {
  const meta = PAGE_META.agent;
  const [tool, setTool] = useState('grc.list_controls');
  const [sessionId, setSessionId] = useState('console-session');
  const [args, setArgs] = useState(DEFAULT_ARGS['grc.list_controls'] ?? '{}');
  const [approvalToken, setApprovalToken] = useState('');
  const [idempotencyKey, setIdempotencyKey] = useState('');
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function pickTool(name: string) {
    setTool(name);
    setArgs(DEFAULT_ARGS[name] ?? '{}');
  }

  async function invoke() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const parsed = JSON.parse(args) as Record<string, unknown>;
      const res = await api.agentInvoke({
        sessionId,
        tool,
        args: parsed,
        approvalToken: approvalToken || undefined,
        idempotencyKey: idempotencyKey || undefined,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? `${e.message}: ${JSON.stringify(e.body)}` : String(e));
    } finally {
      setLoading(false);
    }
  }

  const selected = BUILTIN_TOOLS.find((t) => t.name === tool);

  return (
    <PageShell meta={meta}>
      <div className="card section-gap">
        <div className="form-row">
          <label htmlFor="tool">Agent tool</label>
          <select id="tool" value={tool} onChange={(e) => pickTool(e.target.value)}>
            {BUILTIN_TOOLS.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name} ({t.tier})
              </option>
            ))}
          </select>
          {selected && (
            <>
              <span className={`badge ${selected.tier}`}>{selected.tier}</span>
              <p className="field-hint">{TIER_HELP[selected.tier]}</p>
            </>
          )}
        </div>
        <div className="grid-2">
          <div className="form-row">
            <label htmlFor="session">Session ID (audit correlation)</label>
            <input id="session" value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
          </div>
          <div className="form-row">
            <label htmlFor="idem">Idempotency key (write tier)</label>
            <input
              id="idem"
              value={idempotencyKey}
              onChange={(e) => setIdempotencyKey(e.target.value)}
              placeholder="unique-key-per-mutation"
            />
          </div>
        </div>
        <div className="form-row">
          <label htmlFor="approval">Approval token (destructive tier only)</label>
          <input
            id="approval"
            value={approvalToken}
            onChange={(e) => setApprovalToken(e.target.value)}
            placeholder="Required for SOAR / firewall tools"
          />
        </div>
        <div className="form-row">
          <label htmlFor="args">Tool arguments (JSON)</label>
          <textarea id="args" value={args} onChange={(e) => setArgs(e.target.value)} />
        </div>
        <div className="actions">
          <button type="button" className="primary" onClick={() => void invoke()} disabled={loading}>
            {loading ? 'Invoking…' : 'Invoke tool'}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        {result != null && (
          <>
            <h3 className="result-heading">Decision + audit log</h3>
            <JsonBlock data={result} />
          </>
        )}
      </div>

      <div className="card">
        <h2>Exec policy reference</h2>
        <table>
          <thead>
            <tr>
              <th>Tool</th>
              <th>Tier</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {BUILTIN_TOOLS.map((t) => (
              <tr key={t.name}>
                <td>
                  <code>{t.name}</code>
                </td>
                <td>
                  <span className={`badge ${t.tier}`}>{t.tier}</span>
                </td>
                <td className="muted-cell">{TIER_HELP[t.tier]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PageShell>
  );
}
