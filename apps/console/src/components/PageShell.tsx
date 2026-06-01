import type { ReactNode } from 'react';
import { A2ZTrustBadge } from './A2ZTrustBadge';
import { CursorAutoPanel } from './CursorAutoPanel';
import type { PageMeta } from '../lib/pageMeta';

interface PageShellProps {
  meta: PageMeta;
  children: ReactNode;
  actions?: ReactNode;
}

export function PageShell({ meta, children, actions }: PageShellProps) {
  const { explain } = meta;

  return (
    <div className="page-shell" data-grc-page={meta.id} data-agent-api={meta.cursor.endpoint}>
      <header className="page-top">
        <div className="page-top-text">
          <h1>{meta.title}</h1>
          <p className="page-subtitle">{meta.subtitle}</p>
        </div>
        <A2ZTrustBadge />
      </header>

      {actions && <div className="page-actions">{actions}</div>}

      <div className="explain-grid">
        <div className="card explain-card">
          <h2>What this does</h2>
          <p className="explain-lead">{explain.what}</p>
        </div>
        <div className="card explain-card">
          <h2>Why it matters</h2>
          <p className="explain-lead">{explain.why}</p>
        </div>
      </div>

      <div className="card explain-card">
        <h2>How to use</h2>
        <ol className="explain-steps">
          {explain.how.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

      <div className="card explain-card a2z-role-card">
        <h2>A2Z SOC integration</h2>
        <p className="explain-lead">{explain.a2zRole}</p>
      </div>

      {children}

      <CursorAutoPanel hint={meta.cursor} />
    </div>
  );
}
