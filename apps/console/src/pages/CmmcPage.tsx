import { useState } from 'react';
import { api, ApiError } from '../lib/api';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';
import { JsonBlock } from '../components/JsonBlock';

export function CmmcPage() {
  const meta = PAGE_META.cmmc;
  const [activeTab, setActiveTab] = useState<'levels' | 'boundary' | 'sovereign' | 'evidence'>('levels');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // System Boundary Auditor Inputs
  const [mfaEnabled, setMfaEnabled] = useState(true);
  const [sessionTimeout, setSessionTimeout] = useState(600);
  const [remoteAccessEncrypted, setRemoteAccessEncrypted] = useState(true);
  const [auditLogsForwarded, setAuditLogsForwarded] = useState(true);
  const [boundaryResult, setBoundaryResult] = useState<unknown>(null);

  // Sovereign Compute Auditor Inputs
  const [hostCpu, setHostCpu] = useState('Nvidia Vera ARM CPU');
  const [gpuHardware, setGpuHardware] = useState('Nvidia Blackwell GB200 NVL72');
  const [airgapStatus, setAirgapStatus] = useState('FULLY_AIRGAPPED');
  const [modelWeightsSource, setModelWeightsSource] = useState('LOCAL_AUDITED_WEIGHTS');
  const [nemoGuardrailsActive, setNemoGuardrailsActive] = useState(true);
  const [sovereignResult, setSovereignResult] = useState<unknown>(null);

  // Evidence Generator Inputs
  const [logsCount, setLogsCount] = useState(15);
  const [sodCount, setSodCount] = useState(2);
  const [evidenceResult, setEvidenceResult] = useState<unknown>(null);

  const runBoundaryAudit = async () => {
    setLoading(true);
    setError(null);
    setBoundaryResult(null);
    try {
      const payload = {
        sessionId: `console-boundary-${Date.now()}`,
        tool: 'cmmc.validate_system_boundary',
        args: {
          systemBaseline: {
            mfaEnabled,
            sessionTimeoutSeconds: Number(sessionTimeout),
            remoteAccessEncrypted,
            auditLogsForwarded
          }
        }
      };
      const res = await api.agentInvoke(payload);
      setBoundaryResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Boundary audit failed');
    } finally {
      setLoading(false);
    }
  };

  const runSovereignAudit = async () => {
    setLoading(true);
    setError(null);
    setSovereignResult(null);
    try {
      const payload = {
        sessionId: `console-sovereign-${Date.now()}`,
        tool: 'sovereign.verify_compute_boundary',
        args: {
          hostCpu,
          gpuHardware,
          airgapStatus,
          modelWeightsSource,
          nemoGuardrailsActive
        }
      };
      const res = await api.agentInvoke(payload);
      setSovereignResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Sovereign audit failed');
    } finally {
      setLoading(false);
    }
  };

  const runEvidenceGen = async () => {
    setLoading(true);
    setError(null);
    setEvidenceResult(null);
    try {
      // Build mock logs and violations based on inputs
      const sessionLogs = Array.from({ length: Number(logsCount) }, (_, i) => ({
        sessionId: `session-log-${100 + i}`,
        actionsCount: Math.floor(Math.random() * 15) + 1
      }));
      const sodViolations = Array.from({ length: Number(sodCount) }, (_, i) => ({
        ruleName: 'Dev-Review SoD Conflict',
        timestamp: new Date(Date.now() - i * 3600000).toISOString()
      }));

      const payload = {
        sessionId: `console-evidence-${Date.now()}`,
        idempotencyKey: `idem-evidence-${Date.now()}`,
        tool: 'cmmc.generate_audit_evidence',
        args: {
          sessionLogs,
          sodViolations
        }
      };
      const res = await api.agentInvoke(payload);
      setEvidenceResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Evidence generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell meta={meta}>
      <div className="tabs">
        <button type="button" className={activeTab === 'levels' ? 'active' : ''} onClick={() => setActiveTab('levels')}>
          CMMC 3 Levels
        </button>
        <button type="button" className={activeTab === 'boundary' ? 'active' : ''} onClick={() => setActiveTab('boundary')}>
          Boundary Auditor
        </button>
        <button type="button" className={activeTab === 'sovereign' ? 'active' : ''} onClick={() => setActiveTab('sovereign')}>
          Sovereign Compute
        </button>
        <button type="button" className={activeTab === 'evidence' ? 'active' : ''} onClick={() => setActiveTab('evidence')}>
          Evidence Vault
        </button>
      </div>

      {error && <p className="error section-gap">{error}</p>}
      {loading && <p className="muted-text section-gap">Interacting with GRC_Claw Gateway daemon...</p>}

      {activeTab === 'levels' && (
        <div className="section-gap">
          <div className="card section-gap">
            <h2>A2Z SOC GRC MCP: Unified CMMC Controls</h2>
            <p className="explain-lead">
              The <strong>A2Z SOC GRC MCP</strong> comes pre-configured with all CMMC 2.0 control points mapped to direct system telemetry. This enables continuous verification and real-time posture reporting on the primary dashboard.
            </p>
          </div>

          <div className="grid-3 section-gap">
            <div className="card">
              <span className="badge ok">Level 1: Foundational</span>
              <h3 style={{ marginTop: '0.5rem' }}>17 Practices</h3>
              <p className="muted-text" style={{ fontSize: '0.9rem' }}>
                Establishes basic safeguarding requirements for Federal Contract Information (FCI). Focuses on access controls, authentication, and physical security.
              </p>
              <ul className="field-hint" style={{ paddingLeft: '1rem', marginTop: '0.5rem' }}>
                <li>Basic Access Controls</li>
                <li>Sanitization of Media</li>
                <li>Physical Access Control</li>
              </ul>
            </div>

            <div className="card">
              <span className="badge warning">Level 2: Advanced</span>
              <h3 style={{ marginTop: '0.5rem' }}>110 Practices</h3>
              <p className="muted-text" style={{ fontSize: '0.9rem' }}>
                Aligned completely with <strong>NIST SP 800-171</strong>. Mandatory for any contractor handling Controlled Unclassified Information (CUI).
              </p>
              <ul className="field-hint" style={{ paddingLeft: '1rem', marginTop: '0.5rem' }}>
                <li>Multi-Factor Authentication (MFA)</li>
                <li>15-Minute Session Timeouts</li>
                <li>Audit Log Forwarding (SIEM)</li>
              </ul>
            </div>

            <div className="card">
              <span className="badge read">Level 3: Expert</span>
              <h3 style={{ marginTop: '0.5rem' }}>24+ Practices</h3>
              <p className="muted-text" style={{ fontSize: '0.9rem' }}>
                Aligned with <strong>NIST SP 800-172</strong>. Guards against Advanced Persistent Threats (APTs) using high-security sovereign architectures.
              </p>
              <ul className="field-hint" style={{ paddingLeft: '1rem', marginTop: '0.5rem' }}>
                <li>Sovereign Compute Boundaries</li>
                <li>Airgapped Silicon Audit</li>
                <li>NeMo Real-time Guardrails</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'boundary' && (
        <div className="grid-2 section-gap">
          <div className="card">
            <h2>CMMC Level 2 Boundary Config</h2>
            <p className="field-hint">Configure system parameters to test against NIST SP 800-171 controls.</p>
            
            <div className="form-row" style={{ marginTop: '1rem' }}>
              <label>
                <input type="checkbox" checked={mfaEnabled} onChange={(e) => setMfaEnabled(e.target.checked)} />
                Enforce Multi-Factor Authentication (MFA)
              </label>
            </div>

            <div className="form-row">
              <label htmlFor="timeout-input">Session Timeout (seconds)</label>
              <input
                id="timeout-input"
                type="number"
                value={sessionTimeout}
                onChange={(e) => setSessionTimeout(Number(e.target.value))}
              />
              <p className="field-hint">CMMC requires session timeouts &le; 900s (15 minutes).</p>
            </div>

            <div className="form-row">
              <label>
                <input type="checkbox" checked={remoteAccessEncrypted} onChange={(e) => setRemoteAccessEncrypted(e.target.checked)} />
                Enforce Remote Access Encryption (TLS/SSH)
              </label>
            </div>

            <div className="form-row">
              <label>
                <input type="checkbox" checked={auditLogsForwarded} onChange={(e) => setAuditLogsForwarded(e.target.checked)} />
                Forward Audit Logs to SIEM (Ingest normalizer)
              </label>
            </div>

            <button type="button" className="btn btn-primary" onClick={runBoundaryAudit}>
              Audit Boundary Compliance
            </button>
          </div>

          <div className="card">
            <h2>Audit Outcome</h2>
            {boundaryResult ? (
              <div>
                <span className={`badge ${((boundaryResult as any).output?.complianceStatus === 'COMPLIANT') ? 'ok' : 'destructive'}`} style={{ marginBottom: '1rem' }}>
                  {((boundaryResult as any).output?.complianceStatus ?? 'UNKNOWN')}
                </span>
                <JsonBlock data={boundaryResult} />
              </div>
            ) : (
              <p className="muted-text">Run the audit tool to evaluate boundary parameters against GRC_Claw policy.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'sovereign' && (
        <div className="grid-2 section-gap">
          <div className="card">
            <h2>Sovereign Airgapped Compute Boundary</h2>
            <p className="field-hint">Verify local silicon and weights isolation against NIST SP 800-172 / Level 3 controls.</p>

            <div className="form-row" style={{ marginTop: '1rem' }}>
              <label htmlFor="cpu-input">Host CPU System</label>
              <select id="cpu-input" value={hostCpu} onChange={(e) => setHostCpu(e.target.value)}>
                <option value="Nvidia Vera ARM CPU">Nvidia Vera ARM CPU (Certified)</option>
                <option value="Nvidia RTX Spark CPU">Nvidia RTX Spark CPU (Certified Workstation)</option>
                <option value="AMD EPYC Node (Cloud VM)">AMD EPYC Node (Cloud VM - Uncertified)</option>
                <option value="Intel Xeon Processor">Intel Xeon Processor (Local Server)</option>
              </select>
            </div>

            <div className="form-row">
              <label htmlFor="gpu-input">GPU Architecture</label>
              <select id="gpu-input" value={gpuHardware} onChange={(e) => setGpuHardware(e.target.value)}>
                <option value="Nvidia Blackwell GB200 NVL72">Nvidia Blackwell GB200 NVL72 (Certified)</option>
                <option value="Nvidia H200 HBM3e GPU">Nvidia H200 HBM3e GPU (Certified)</option>
                <option value="Cloud GPU Instance (Transient Shared)">Cloud GPU Instance (Shared - Uncertified)</option>
                <option value="Nvidia RTX Spark Workstation GPU">Nvidia RTX Spark Workstation GPU (Certified)</option>
              </select>
            </div>

            <div className="form-row">
              <label htmlFor="airgap-input">Airgap Status</label>
              <select id="airgap-input" value={airgapStatus} onChange={(e) => setAirgapStatus(e.target.value)}>
                <option value="FULLY_AIRGAPPED">Fully Airgapped Node (Certified)</option>
                <option value="CONNECTED_TO_CLOUD">Connected to Public Cloud (Uncertified)</option>
              </select>
            </div>

            <div className="form-row">
              <label htmlFor="weights-input">Model Weights Source</label>
              <select id="weights-input" value={modelWeightsSource} onChange={(e) => setModelWeightsSource(e.target.value)}>
                <option value="LOCAL_AUDITED_WEIGHTS">Local Audited & Frozen Weights (Certified)</option>
                <option value="CLOUD_API_RENTAL">Cloud API Model Rental (Uncertified)</option>
              </select>
            </div>

            <div className="form-row">
              <label>
                <input type="checkbox" checked={nemoGuardrailsActive} onChange={(e) => setNemoGuardrailsActive(e.target.checked)} />
                NeMo Guardrails Active (Local API Gate)
              </label>
            </div>

            <button type="button" className="btn btn-primary" onClick={runSovereignAudit}>
              Audit Sovereign Compute
            </button>
          </div>

          <div className="card">
            <h2>Sovereign Audit Outcome</h2>
            {sovereignResult ? (
              <div>
                <span className={`badge ${((sovereignResult as any).output?.complianceStatus === 'COMPLIANT') ? 'ok' : 'destructive'}`} style={{ marginBottom: '1rem' }}>
                  {((sovereignResult as any).output?.complianceStatus ?? 'UNKNOWN')}
                </span>
                <JsonBlock data={sovereignResult} />
              </div>
            ) : (
              <p className="muted-text">Run the sovereign audit tool to evaluate silicon and airgap parameters.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'evidence' && (
        <div className="grid-2 section-gap">
          <div className="card">
            <h2>C3PAO Audit Evidence Generator</h2>
            <p className="field-hint">Package and sign local compliance traces for official assessments.</p>

            <div className="form-row" style={{ marginTop: '1rem' }}>
              <label htmlFor="logs-count">Active Session Logs to Hash</label>
              <input
                id="logs-count"
                type="number"
                value={logsCount}
                onChange={(e) => setLogsCount(Number(e.target.value))}
              />
            </div>

            <div className="form-row">
              <label htmlFor="sod-count">Recorded SoD Violations to Bundle</label>
              <input
                id="sod-count"
                type="number"
                value={sodCount}
                onChange={(e) => setSodCount(Number(e.target.value))}
              />
            </div>

            <button type="button" className="btn btn-primary" onClick={runEvidenceGen}>
              Generate Cryptographic Evidence Package
            </button>
          </div>

          <div className="card">
            <h2>Generated Proof Bundle</h2>
            {evidenceResult ? (
              <div>
                <span className="badge ok" style={{ marginBottom: '1rem' }}>
                  SIGNED
                </span>
                <div style={{ padding: '0.5rem', background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: '4px', marginBottom: '1rem' }}>
                  <p style={{ fontSize: '0.85rem', margin: '0 0 0.25rem 0' }}><strong>Root Hash:</strong> <code>{(evidenceResult as any).output?.evidenceHash}</code></p>
                  <p style={{ fontSize: '0.85rem', margin: 0 }}><strong>Signature:</strong> <code>{(evidenceResult as any).output?.signature}</code></p>
                </div>
                <JsonBlock data={evidenceResult} />
              </div>
            ) : (
              <p className="muted-text">Generate a proof bundle to calculate Merkle-like root hashes and cryptographic signatures.</p>
            )}
          </div>
        </div>
      )}
    </PageShell>
  );
}
