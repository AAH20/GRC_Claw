import { useState } from 'react';
import { api, ApiError } from '../lib/api';
import { loadSettings } from '../lib/settings';
import { CLOUD_SOURCES, OSS_SOURCES, SAMPLE_PAYLOADS } from '../lib/constants';
import { JsonBlock } from '../components/JsonBlock';
import { PageShell } from '../components/PageShell';
import { PAGE_META } from '../lib/pageMeta';

const SOURCE_HINTS: Record<string, string> = {
  suricata: 'Suricata EVE JSON — network intrusion alerts with signature and severity.',
  wazuh: 'Wazuh rule JSON — host IDS with rule level mapped to critical/high/medium.',
  aws_guardduty: 'AWS GuardDuty finding via EventBridge detail object.',
  azure_sentinel: 'Microsoft Sentinel incident resource with properties.title and severity.',
};

export function IngestPage() {
  const meta = PAGE_META.ingest;
  const [tab, setTab] = useState<'oss' | 'cloud'>('oss');
  const [source, setSource] = useState<string>('suricata');
  const [payload, setPayload] = useState(JSON.stringify(SAMPLE_PAYLOADS.suricata, null, 2));
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const sources = tab === 'oss' ? OSS_SOURCES : CLOUD_SOURCES;

  function pickSource(s: string) {
    setSource(s);
    const sample = SAMPLE_PAYLOADS[s];
    if (sample) setPayload(JSON.stringify(sample, null, 2));
  }

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const parsed = JSON.parse(payload) as unknown;
      const tenantId = loadSettings().tenantId;
      const res = await api.ingestNormalize({ source, tenantId, payload: parsed });
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? `${e.message}: ${JSON.stringify(e.body)}` : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell meta={meta}>
      <div className="tabs">
        <button type="button" className={tab === 'oss' ? 'active' : ''} onClick={() => setTab('oss')}>
          OSS SIEM / IDS ({OSS_SOURCES.length})
        </button>
        <button type="button" className={tab === 'cloud' ? 'active' : ''} onClick={() => setTab('cloud')}>
          Multi-cloud ({CLOUD_SOURCES.length})
        </button>
      </div>

      <div className="card section-gap">
        <p className="explain-lead">
          {tab === 'oss'
            ? 'Open-source stack: Wazuh, Suricata, Snort, Elastic ECS, and UFW firewall logs.'
            : 'AWS GuardDuty/CloudWatch/Security Hub/CloudTrail, Azure Sentinel/Defender/Monitor, GCP Chronicle/SCC/Logging.'}
        </p>
        <div className="form-row">
          <label htmlFor="source">Source system</label>
          <select id="source" value={source} onChange={(e) => pickSource(e.target.value)}>
            {sources.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          {SOURCE_HINTS[source] && <p className="field-hint">{SOURCE_HINTS[source]}</p>}
        </div>
        <div className="form-row">
          <label htmlFor="payload">Vendor payload (JSON)</label>
          <textarea id="payload" value={payload} onChange={(e) => setPayload(e.target.value)} rows={14} />
        </div>
        <div className="actions">
          <button type="button" className="primary" onClick={() => void run()} disabled={loading}>
            {loading ? 'Normalizing…' : 'Normalize & map to controls'}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        {result != null && (
          <>
            <h3 className="result-heading">Normalized event + compliance impact</h3>
            <p className="explain-lead">
              Review <code>event.eventType</code>, <code>event.severity</code>, and{' '}
              <code>complianceImpact.controlIds</code> — these drive A2Z SOC analyst queues when the
              bridge is active.
            </p>
            <JsonBlock data={result} />
          </>
        )}
      </div>
    </PageShell>
  );
}
