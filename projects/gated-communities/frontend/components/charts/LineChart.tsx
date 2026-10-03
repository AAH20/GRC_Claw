'use client';

import React from 'react';

export interface LineChartDataPoint {
  label: string;
  value: number;
}

export interface LineChartProps {
  data: LineChartDataPoint[];
  width?: number;
  height?: number;
  strokeColor?: string;
  fillColor?: string;
  strokeWidth?: number;
  showDots?: boolean;
  showGrid?: boolean;
  showLabels?: boolean;
  className?: string;
  ariaLabel?: string;
}

const LineChart: React.FC<LineChartProps> = ({
  data,
  width = 600,
  height = 300,
  strokeColor = '#3b82f6',
  fillColor = 'rgba(59, 130, 246, 0.1)',
  strokeWidth = 2,
  showDots = true,
  showGrid = true,
  showLabels = true,
  className = '',
  ariaLabel = 'Line chart',
}) => {
  if (data.length === 0) {
    return (
      <div className={`flex items-center justify-center text-gray-400 ${className}`} style={{ width, height }}>
        No data available
      </div>
    );
  }

  const padding = { top: 20, right: 20, bottom: showLabels ? 40 : 20, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const maxValue = Math.max(...data.map((d) => d.value));
  const minValue = Math.min(...data.map((d) => d.value));
  const valueRange = maxValue - minValue || 1;

  const xStep = chartWidth / Math.max(data.length - 1, 1);

  const points = data.map((d, i) => ({
    x: padding.left + i * xStep,
    y: padding.top + chartHeight - ((d.value - minValue) / valueRange) * chartHeight,
    ...d,
  }));

  const pathD = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ');

  const areaD = `${pathD} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`;

  const gridLines = showGrid
    ? Array.from({ length: 5 }, (_, i) => {
        const y = padding.top + (chartHeight / 4) * i;
        const value = maxValue - (valueRange / 4) * i;
        return { y, value: Math.round(value * 100) / 100 };
      })
    : [];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      role="img"
      aria-label={ariaLabel}
    >
      {/* Grid lines */}
      {gridLines.map((line, i) => (
        <g key={i}>
          <line
            x1={padding.left}
            y1={line.y}
            x2={width - padding.right}
            y2={line.y}
            stroke="#e5e7eb"
            strokeDasharray="4 4"
          />
          {showLabels && (
            <text
              x={padding.left - 8}
              y={line.y + 4}
              textAnchor="end"
              className="fill-gray-500 text-xs"
            >
              {line.value}
            </text>
          )}
        </g>
      ))}

      {/* Area fill */}
      <path d={areaD} fill={fillColor} />

      {/* Line */}
      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Dots */}
      {showDots &&
        points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={4}
            fill={strokeColor}
            stroke="#fff"
            strokeWidth={2}
          />
        ))}

      {/* X-axis labels */}
      {showLabels &&
        points.map((p, i) => (
          <text
            key={i}
            x={p.x}
            y={height - 8}
            textAnchor="middle"
            className="fill-gray-500 text-xs"
          >
            {p.label}
          </text>
        ))}
    </svg>
  );
};

export default LineChart;
