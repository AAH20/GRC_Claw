interface ComplianceGaugeProps {
  score: number;
}

export function ComplianceGauge({ score }: ComplianceGaugeProps) {
  const clamped = Math.max(0, Math.min(100, score));
  const color =
    clamped < 60 ? 'var(--danger)' : clamped < 80 ? 'var(--warn)' : 'var(--success)';

  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div className="compliance-gauge">
      <svg viewBox="0 0 100 100" className="gauge-svg">
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth="10"
        />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
        <text x="50" y="46" textAnchor="middle" className="gauge-value" fill="var(--text)">
          {clamped}
        </text>
        <text x="50" y="60" textAnchor="middle" className="gauge-unit" fill="var(--text-muted)">
          / 100
        </text>
      </svg>
    </div>
  );
}
