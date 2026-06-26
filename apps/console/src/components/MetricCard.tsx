interface MetricCardProps {
  name: string;
  value: number | string;
  trend?: { direction: 'up' | 'down'; percentage: number };
  sparkline?: number[];
}

export function MetricCard({ name, value, trend, sparkline }: MetricCardProps) {
  const displayValue = typeof value === 'number' ? value.toLocaleString() : value;

  return (
    <div className="metric-card">
      <div className="metric-card-label">{name}</div>
      <div className="metric-card-value">{displayValue}</div>
      {trend && (
        <div className={`metric-card-trend ${trend.direction}`}>
          <span className="trend-arrow">{trend.direction === 'up' ? '\u2191' : '\u2193'}</span>
          <span className="trend-pct">{Math.abs(trend.percentage)}%</span>
        </div>
      )}
      {sparkline && sparkline.length > 1 && (
        <svg className="metric-sparkline" viewBox="0 0 100 30" preserveAspectRatio="none">
          <polyline
            fill="none"
            stroke="var(--accent)"
            strokeWidth="2"
            points={sparkline
              .map((v, i) => {
                const min = Math.min(...sparkline);
                const max = Math.max(...sparkline);
                const range = max - min || 1;
                const x = (i / (sparkline.length - 1)) * 100;
                const y = 30 - ((v - min) / range) * 28 - 1;
                return `${x},${y}`;
              })
              .join(' ')}
          />
        </svg>
      )}
    </div>
  );
}
