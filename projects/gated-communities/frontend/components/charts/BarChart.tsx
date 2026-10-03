'use client';

import React from 'react';

export interface BarChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface BarChartProps {
  data: BarChartDataPoint[];
  width?: number;
  height?: number;
  barColor?: string;
  showGrid?: boolean;
  showLabels?: boolean;
  showValues?: boolean;
  horizontal?: boolean;
  className?: string;
  ariaLabel?: string;
}

const BarChart: React.FC<BarChartProps> = ({
  data,
  width = 600,
  height = 300,
  barColor = '#3b82f6',
  showGrid = true,
  showLabels = true,
  showValues = true,
  horizontal = false,
  className = '',
  ariaLabel = 'Bar chart',
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
  const valueRange = maxValue || 1;

  const gridLines = showGrid
    ? Array.from({ length: 5 }, (_, i) => {
        const ratio = i / 4;
        return horizontal
          ? { x: padding.left + chartWidth * ratio, value: Math.round(valueRange * ratio * 100) / 100 }
          : { y: padding.top + chartHeight * (1 - ratio), value: Math.round(valueRange * ratio * 100) / 100 };
      })
    : [];

  if (horizontal) {
    const barHeight = chartHeight / data.length;
    const barGap = barHeight * 0.2;

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
              x1={line.x}
              y1={padding.top}
              x2={line.x}
              y2={height - padding.bottom}
              stroke="#e5e7eb"
              strokeDasharray="4 4"
            />
            {showLabels && (
              <text x={line.x} y={height - 8} textAnchor="middle" className="fill-gray-500 text-xs">
                {line.value}
              </text>
            )}
          </g>
        ))}

        {/* Bars */}
        {data.map((d, i) => {
          const barWidth = (d.value / valueRange) * chartWidth;
          const y = padding.top + i * barHeight + barGap / 2;
          return (
            <g key={i}>
              <rect
                x={padding.left}
                y={y}
                width={barWidth}
                height={barHeight - barGap}
                fill={d.color || barColor}
                rx={4}
              />
              {showValues && (
                <text
                  x={padding.left + barWidth + 6}
                  y={y + (barHeight - barGap) / 2 + 4}
                  className="fill-gray-600 text-xs"
                >
                  {d.value}
                </text>
              )}
              {showLabels && (
                <text
                  x={padding.left - 8}
                  y={y + (barHeight - barGap) / 2 + 4}
                  textAnchor="end"
                  className="fill-gray-500 text-xs"
                >
                  {d.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    );
  }

  const barWidth = chartWidth / data.length;
  const barGap = barWidth * 0.2;

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
            <text x={padding.left - 8} y={line.y + 4} textAnchor="end" className="fill-gray-500 text-xs">
              {line.value}
            </text>
          )}
        </g>
      ))}

      {/* Bars */}
      {data.map((d, i) => {
        const barHeight = (d.value / valueRange) * chartHeight;
        const x = padding.left + i * barWidth + barGap / 2;
        const y = padding.top + chartHeight - barHeight;
        return (
          <g key={i}>
            <rect x={x} y={y} width={barWidth - barGap} height={barHeight} fill={d.color || barColor} rx={4} />
            {showValues && (
              <text x={x + (barWidth - barGap) / 2} y={y - 6} textAnchor="middle" className="fill-gray-600 text-xs">
                {d.value}
              </text>
            )}
            {showLabels && (
              <text
                x={x + (barWidth - barGap) / 2}
                y={height - 8}
                textAnchor="middle"
                className="fill-gray-500 text-xs"
              >
                {d.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

export default BarChart;
