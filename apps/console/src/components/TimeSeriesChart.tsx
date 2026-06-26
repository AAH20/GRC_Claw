interface DataPoint {
  label: string;
  value: number;
}

interface TimeSeriesChartProps {
  data: DataPoint[];
  height?: number;
}

export function TimeSeriesChart({ data, height = 150 }: TimeSeriesChartProps) {
  if (data.length === 0) return <div className="time-series-empty">No data</div>;

  const values = data.map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const padding = { top: 10, right: 10, bottom: 25, left: 40 };
  const width = 300;
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  const points = data.map((d, i) => {
    const x = padding.left + (i / (data.length - 1 || 1)) * innerW;
    const y = padding.top + innerH - ((d.value - min) / range) * innerH;
    return { x, y, label: d.label };
  });

  const gridLines = 4;
  const ticks = Array.from({ length: gridLines + 1 }, (_, i) => {
    const val = min + (range * i) / gridLines;
    const y = padding.top + innerH - (i / gridLines) * innerH;
    return { y, label: Math.round(val) };
  });

  return (
    <svg className="time-series-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      {ticks.map((tick, i) => (
        <g key={i}>
          <line
            x1={padding.left}
            y1={tick.y}
            x2={width - padding.right}
            y2={tick.y}
            stroke="var(--border)"
            strokeDasharray="3,3"
          />
          <text x={padding.left - 5} y={tick.y + 4} textAnchor="end" fill="var(--text-muted)" fontSize="8">
            {tick.label}
          </text>
        </g>
      ))}
      <polyline
        fill="none"
        stroke="var(--accent)"
        strokeWidth="2"
        points={points.map((p) => `${p.x},${p.y}`).join(' ')}
      />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3" fill="var(--accent)" />
      ))}
      {points.length <= 10 &&
        points.map((p, i) => (
          <text
            key={`lbl-${i}`}
            x={p.x}
            y={height - 5}
            textAnchor="middle"
            fill="var(--text-muted)"
            fontSize="7"
          >
            {data[i].label}
          </text>
        ))}
    </svg>
  );
}
