import { useState } from 'react';
import { loadSettings } from '../lib/settings';
import { buildCurl, CURSOR_AUTO_RULES, CURSOR_MCP_SNIPPET } from '../lib/cursorAuto';
import type { CursorAutoHint } from '../lib/pageMeta';

export function CopyBlock({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* fallback ignored */
    }
  }

  return (
    <div className="copy-block">
      {label && <div className="copy-block-label">{label}</div>}
      <pre className="json-block copy-block-pre">{text}</pre>
      <button type="button" className="copy-btn" onClick={() => void copy()}>
        {copied ? 'Copied' : 'Copy'}
      </button>
    </div>
  );
}

export function CursorAutoPanel({ hint }: { hint: CursorAutoHint }) {
  const settings = loadSettings();
  if (!settings.cursorAutoMode) return null;

  const curl = buildCurl(hint);

  return (
    <div className="card cursor-auto-panel" data-agent-panel="cursor-auto">
      <h2>Cursor Auto Mode</h2>
      <p className="explain-lead">
        Agents and automations can call this page&apos;s API directly. Use the snippets below in
        Cursor Agent or Automations — policy gates still apply on the gateway.
      </p>
      <div className="cursor-auto-grid">
        <div>
          <div className="detail-label">Endpoint</div>
          <code>
            {hint.method} {hint.endpoint}
          </code>
          {hint.auth && <span className="badge write" style={{ marginLeft: '0.5rem' }}>auth</span>}
        </div>
        <div>
          <div className="detail-label">Agent instruction</div>
          <p className="explain-lead">{hint.agentInstruction}</p>
        </div>
      </div>
      <CopyBlock text={curl} label="curl" />
      <details className="cursor-details">
        <summary>MCP / rules reference</summary>
        <CopyBlock text={CURSOR_MCP_SNIPPET} label="Cursor MCP config (HTTP gateway)" />
        <CopyBlock text={CURSOR_AUTO_RULES} label="Auto Mode rules" />
        <p className="explain-lead">
          Full API map:{' '}
          <a href="/llms.txt" target="_blank" rel="noreferrer">
            /llms.txt
          </a>
        </p>
      </details>
    </div>
  );
}
