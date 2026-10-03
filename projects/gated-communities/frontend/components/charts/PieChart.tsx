'use client';

import React from 'react';

export interface PieChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface PieChartProps {
  data: PieChartDataPoint[];
  width?: number;
  height?: number;
  colors?: string[];
  showLabels?: boolean;
  showLegend?: boolean;
  showPercentages?: boolean;
  donut?: boolean;
  donutThickness?: number;
  className?: string;
  ariaLabel?: string;
}

const DEFAULT_COLORS = [
  '#3b82f6',
  '#ef4444',
  '#10b981',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
  '#84cc16',
];

const PieChart: React.FC<PieChartProps> = ({
  data,
  width = 400,
  height = 300,
  colors = DEFAULT_COLORS,
  showLabels = true,
  showLegend = true,
  showPercentages = true,
  donut = false,
  donutThickness = 40,
  className = '',
  ariaLabel = 'Pie chart',
}) => {
  if (data.length === 0) {
    return (
      <div className={`flex items-center justify-center text-gray-400 ${className}`} style={{ width, height }}>
        No data available
      </div>
    );
  }

  const total = data.reduce((sum, d) => sum + d.value, 0);
  const centerX = showLegend ? width * 0.35 : width / 2;
  const centerY = height / 2;
  const radius = Math.min(centerX, centerY) - 20;
  const innerRadius = donut ? radius - donutThickness : 0;

  let currentAngle = -Math.PI / 2;

  const slices = data.map((d, i) => {
    const sliceAngle = (d.value / total) * 2 * Math.PI;
    const startAngle = currentAngle;
    const endAngle = currentAngle + sliceAngle;
    currentAngle = endAngle;

    const midAngle = (startAngle + endAngle) / 2;
    const largeArcFlag = sliceAngle > Math.PI ? 1 : 0;

    const x1 = centerX + radius * Math.cos(startAngle);
    const y1 = centerY + radius * Math.sin(startAngle);
    const x2 = centerX + radius * Math.cos(endAngle);
    const y2 = centerY + radius * Math.sin(endAngle);

    let pathD: string;
    if (donut) {
      const ix1 = centerX + innerRadius * Math.cos(startAngle);
      const iy1 = centerY + innerRadius * Math.sin(startAngle);
      const ix2 = centerX + innerRadius * Math.cos(endAngle);
      const iy2 = centerY + innerRadius * Math.sin(endAngle);

      pathD = [
        `M ${x1} ${y1}`,
        `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
        `L ${ix2} ${iy2}`,
        `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${ix1} ${iy1}`,
        'Z',
      ].join(' ');
    } else {
      pathD = [`M ${centerX} ${centerY}`, `L ${x1} ${y1}`, `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`, 'Z'].join(' ');
    }

    const labelRadius = donut ? (radius + innerRadius) / 2 : radius * 0.7;
    const labelX = centerX + labelRadius * Math.cos(midAngle);
    const labelY = centerY + labelRadius * Math.sin(midAngle);
    const percentage = Math.round((d.value / total) * 100);

    return {
      ...d,
      color: d.color || colors[i % colors.length],
      pathD,
      labelX,
      labelY,
      percentage,
    };
  });

  return (
    <div className={`flex ${className}`} style={{ width, height }}>
      <svg width={showLegend ? width * 0.7 : width} height={height} role="img" aria-label={ariaLabel}>
        {/* Slices */}
        {slices.map((slice, i) => (
          <path key={i} d={slice.pathD} fill={slice.color} stroke="#fff" strokeWidth={2} />
        ))}

        {/* Labels */}
        {showPercentages &&
          slices.map((slice, i) => (
            <text
              key={i}
              x={slice.labelX}
              y={slice.labelY}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-white text-xs font-medium"
            >
              {slice.percentage}%
            </text>
          ))}
      </svg>

      {/* Legend */}
      {showLegend && showLabels && (
        <div className="flex flex-col justify-center gap-2 pl-4">
          {slices.map((slice, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: slice.color }} />
              <span className="text-sm text-gray-600">{slice.label}</span>
              <span className="text-sm text-gray-400">({slice.value})</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PieChart;
