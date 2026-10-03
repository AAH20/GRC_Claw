'use client';

import React, { useMemo } from 'react';

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
  barRadius?: number;
  showGrid?: boolean;
  showLabels?: boolean;
  showValues?: boolean;
  horizontal?: boolean;
  className?: string;
  yAxisFormatter?: (value: number) => string;
  xAxisFormatter?: (label: string) => string;
}

const DEFAULT_WIDTH = 600;
const DEFAULT_HEIGHT = 300;
const PADDING = { top: 20, right: 20, bottom: 40, left: 50 };

export const BarChart: React.FC<BarChartProps> = ({
  data,
  width = DEFAULT_WIDTH,
  height = DEFAULT_HEIGHT,
  barColor = '#3b82f6',
  barRadius = 4,
  showGrid = true,
  showLabels = true,
  showValues = true,
  horizontal = false,
  className = '',
  yAxisFormatter = (v) => v.toString(),
  xAxisFormatter = (l) => l,
}) => {
  const chartWidth = width - PADDING.left - PADDING.right;
  const chartHeight = height - PADDING.top - PADDING.bottom;

  const { bars, ticks, maxValue } = useMemo(() => {
    if (data.length === 0) {
      return { bars: [], ticks: [], maxValue: 0 };
    }

    const values = data.map((d) => d.value);
    const rawMax = Math.max(...values, 0);
    const paddedMax = rawMax * 1.1 || 1;

    const numTicks = 5;
    const tickValues: number[] = [];
    for (let i = 0; i <= numTicks; i++) {
      tickValues.push((paddedMax * i) / numTicks);
    }

    let computedBars: Array<{
      x: number;
      y: number;
      width: number;
      height: number;
      label: string;
      value: number;
      color: string;
    }>;

    if (horizontal) {
      const barHeight = chartHeight / data.length;
      const barPadding = barHeight * 0.15;
      computedBars = data.map((d, i) => {
        const barW = ((d.value - 0) / paddedMax) * chartWidth;
        return {
          x: PADDING.left,
          y: PADDING.top + i * barHeight + barPadding / 2,
          width: barW,
          height: barHeight - barPadding,
          label: d.label,
          value: d.value,
          color: d.color || barColor,
        };
      });
    } else {
      const barWidth = chartWidth / data.length;
      const barPadding = barWidth * 0.15;
      computedBars = data.map((d, i) => {
        const barH = ((d.value - 0) / paddedMax) * chartHeight;
        return {
          x: PADDING.left + i * barWidth + barPadding / 2,
          y: PADDING.top + chartHeight - barH,
          width: barWidth - barPadding,
          height: barH,
          label: d.label,
          value: d.value,
          color: d.color || barColor,
        };
      });
    }

    return { bars: computedBars, ticks: tickValues, maxValue: paddedMax };
  }, [data, chartWidth, chartHeight, barColor, horizontal]);

  if (data.length === 0) {
    return (
      <div
        className={`flex items-center justify-center text-gray-400 ${className}`}
        style={{ width, height }}
      >
        No data available
      </div>
    );
  }

  return (
    <div className={`inline-block ${className}`}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="overflow-visible"
        role="img"
        aria-label="Bar chart"
      >
        {/* Grid lines */}
        {showGrid &&
          ticks.map((tick, i) => {
            if (horizontal) {
              const x = PADDING.left + (tick / maxValue) * chartWidth;
              return (
                <g key={`grid-${i}`}>
                  <line
                    x1={x}
                    y1={PADDING.top}
                    x2={x}
                    y2={height - PADDING.bottom}
                    stroke="#e5e7eb"
                    strokeDasharray="4 4"
                  />
                  {showLabels && (
                    <text
                      x={x}
                      y={height - PADDING.bottom + 20}
                      textAnchor="middle"
                      className="fill-gray-500 text-xs"
                    >
                      {yAxisFormatter(Math.round(tick * 100) / 100)}
                    </text>
                  )}
                </g>
              );
            }
            const y = PADDING.top + chartHeight - (tick / maxValue) * chartHeight;
            return (
              <g key={`grid-${i}`}>
                <line
                  x1={PADDING.left}
                  y1={y}
                  x2={width - PADDING.right}
                  y2={y}
                  stroke="#e5e7eb"
                  strokeDasharray="4 4"
                />
                {showLabels && (
                  <text
                    x={PADDING.left - 8}
                    y={y + 4}
                    textAnchor="end"
                    className="fill-gray-500 text-xs"
                  >
                    {yAxisFormatter(Math.round(tick * 100) / 100)}
                  </text>
                )}
              </g>
            );
          })}

        {/* Bars */}
        {bars.map((bar, i) => (
          <g key={`bar-${i}`}>
            <rect
              x={bar.x}
              y={bar.y}
              width={bar.width}
              height={bar.height}
              fill={bar.color}
              rx={barRadius}
              ry={barRadius}
            >
              <title>{`${bar.label}: ${bar.value}`}</title>
            </rect>

            {/* Value labels */}
            {showValues && (
              <text
                x={horizontal ? bar.x + bar.width + 6 : bar.x + bar.width / 2}
                y={horizontal ? bar.y + bar.height / 2 + 4 : bar.y - 6}
                textAnchor={horizontal ? 'start' : 'middle'}
                className="fill-gray-600 text-xs font-medium"
              >
                {bar.value}
              </text>
            )}

            {/* Category labels */}
            {showLabels && (
              <text
                x={horizontal ? PADDING.left - 8 : bar.x + bar.width / 2}
                y={
                  horizontal
                    ? bar.y + bar.height / 2 + 4
                    : height - PADDING.bottom + 20
                }
                textAnchor={horizontal ? 'end' : 'middle'}
                className="fill-gray-500 text-xs"
              >
                {xAxisFormatter(bar.label)}
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
};

export default BarChart;
