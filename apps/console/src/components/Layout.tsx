import { Link, Outlet, useLocation } from 'react-router-dom';
import { A2ZTrustBadge } from './A2ZTrustBadge';
import { loadSettings } from '../lib/settings';

const NAV = [
  { path: '/', label: 'Dashboard' },
  { path: '/frameworks', label: 'Frameworks' },
  { path: '/ingest', label: 'Ingest' },
  { path: '/agent', label: 'Agent' },
  { path: '/aims', label: 'ISO 42001' },
  { path: '/connectors', label: 'BYOC' },
  { path: '/cmmc', label: 'CMMC 2.0' },
  { path: '/settings', label: 'Settings' },
];

export function Layout() {
  const loc = useLocation();
  const settings = loadSettings();
  const connected = Boolean(settings.token);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-title">GRC_Claw</div>
          <div className="brand-sub">Operator Console</div>
          <div className="sidebar-badge">
            <A2ZTrustBadge compact />
          </div>
        </div>
        <nav className="sidebar-nav">
          {NAV.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-link ${loc.pathname === item.path ? 'active' : ''}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className={`badge ${connected ? 'ok' : 'destructive'}`}>
            {connected ? 'Gateway token set' : 'No token — Settings'}
          </span>
          {settings.cursorAutoMode && (
            <span className="badge read" style={{ marginTop: '0.35rem' }}>
              Cursor Auto
            </span>
          )}
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
