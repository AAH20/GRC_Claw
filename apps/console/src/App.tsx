import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { FrameworksPage } from './pages/FrameworksPage';
import { IngestPage } from './pages/IngestPage';
import { AgentPage } from './pages/AgentPage';
import { AimsPage } from './pages/AimsPage';
import { ConnectorsPage } from './pages/ConnectorsPage';
import { SettingsPage } from './pages/SettingsPage';
import { CmmcPage } from './pages/CmmcPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="frameworks" element={<FrameworksPage />} />
          <Route path="ingest" element={<IngestPage />} />
          <Route path="agent" element={<AgentPage />} />
          <Route path="aims" element={<AimsPage />} />
          <Route path="connectors" element={<ConnectorsPage />} />
          <Route path="cmmc" element={<CmmcPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="a2z" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
