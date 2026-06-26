interface HeatmapCell {
  likelihood: number;
  impact: number;
  count: number;
}

interface RiskHeatmapProps {
  cells: HeatmapCell[];
}

const SEVERITY_COLORS: Record<string, string> = {
  low: 'var(--success)',
  medium: 'var(--warn)',
  high: '#f97316',
  critical: 'var(--danger)',
};

function getSeverity(likelihood: number, impact: number): string {
  const score = likelihood * impact;
  if (score <= 4) return 'low';
  if (score <= 9) return 'medium';
  if (score <= 16) return 'high';
  return 'critical';
}

function getCount(cells: HeatmapCell[], likelihood: number, impact: number): number {
  return cells.find((c) => c.likelihood === likelihood && c.impact === impact)?.count ?? 0;
}

export function RiskHeatmap({ cells }: RiskHeatmapProps) {
  return (
    <div className="risk-heatmap">
      <div className="heatmap-header">
        <span className="heatmap-axis-label">Impact \u2192</span>
      </div>
      <div className="heatmap-grid">
        <div className="heatmap-y-axis">
          {Array.from({ length: 5 }, (_, i) => 5 - i).map((l) => (
            <div key={l} className="heatmap-y-label">
              {l}
            </div>
          ))}
          <span className="heatmap-axis-label vertical">Likelihood</span>
        </div>
        <div className="heatmap-cells">
          {Array.from({ length: 5 }, (_, _, arr) => arr.length).map((_, rowIdx) => {
            const likelihood = 5 - rowIdx;
            return (
              <div key={likelihood} className="heatmap-row">
                {Array.from({ length: 5 }, (_, colIdx) => {
                  const impact = colIdx + 1;
                  const severity = getSeverity(likelihood, impact);
                  const count = getCount(cells, likelihood, impact);
                  return (
                    <div
                      key={impact}
                      className="heatmap-cell"
                      style={{ backgroundColor: SEVERITY_COLORS[severity] }}
                      title={`L:${likelihood} I:${impact} — ${count} risks`}
                    >
                      {count > 0 ? count : ''}
                    </div>
                  );
                })}
              </div>
            );
          })}
          <div className="heatmap-x-labels">
            {Array.from({ length: 5 }, (_, i) => i + 1).map((i) => (
              <div key={i} className="heatmap-x-label">{i}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
