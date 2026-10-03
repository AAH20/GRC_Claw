'use client';

import React, { useMemo } from 'react';

export interface LineChartDataPoint {
  label: string;
  value: number;
}

export interface LineChartProps {
  data: LineChartDataPoint[];
  width?: number;
  height?: number;
  strokeColor?: string;
  strokeWidth?: number;
  fillColor?: string;
  showDots?: boolean;
  showGrid?: boolean;
  showLabels?: boolean;
  className?: string;
  yAxisFormatter?: (value: number) => string;
  xAxisFormatter?: (label: string) => string;
}

const DEFAULT_WIDTH = 600;
const DEFAULT_HEIGHT = 300;
const PADDING = { top: 20, right: 20, bottom: 40, left: 50 };

export const LineChart: React.FC<LineChartProps> = ({
  data,
  width = DEFAULT_WIDTH,
  height = DEFAULT_HEIGHT,
  strokeColor = '#3b82f6',
  strokeWidth = 2,
  fillColor = 'rgba(59, 130, 246, 0.1)',
  showDots = true,
  showGrid = true,
  showLabels = true,
  className = '',
  yAxisFormatter = (v) => v.toString(),
  xAxisFormatter = (l) => l,
}) => {
  const chartWidth = width - PADDING.left - PADDING.right;
  const chartHeight = height - PADDING.top - PADDING.bottom;

  const { points, yTicks, xTicks, maxValue, minValue } = useMemo(() => {
    if (data.length === 0) {
      return { points: [], yTicks: [], xTicks: [], maxValue: 0, minValue: 0 };
    }

    const values = data.map((d) => d.value);
    const rawMax = Math.max(...values);
    const rawMin = Math.min(...values);
    const range = rawMax - rawMin || 1;
    const paddedMax = rawMax + range * 0.1;
    const paddedMin = Math.max(0, rawMin - range * 0.1);

    const xStep = chartWidth / Math.max(data.length - 1, 1);
    const yStep = chartHeight / Math.max(paddedMax - paddedMin, 1);

    const pts = data.map((d, i) => ({
      x: PADDING.left + i * xStep,
      y: PADDING.top + chartHeight - (d.value - paddedMin) * yStep,
      ...d,
    }));

    const yTickValues: number[] = [];
    const numYTicks = 5;
    for (let i = 0; i <= numYTicks; i++) {
      yTickValues.push(paddedMin + ((paddedMax - paddedMin) * i) / numYTicks);
    }

    const xTickValues = data.map((d, i) => ({
      x: PADDING.left + i * xStep,
      label: d.label,
    }));

    return {
      points: pts,
      yTicks: yTickValues,
      xTicks: xTickValues,
      maxValue: paddedMax,
      minValue: paddedMin,
    };
  }, [data, chartWidth, chartHeight]);

  const pathD = useMemo(() => {
    if (points.length === 0) return '';
    return points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
      .join(' ');
  }, [points]);

  const areaD = useMemo(() => {
    if (points.length === 0) return '';
    const baseline = PADDING.top + chartHeight;
    return `${pathD} L ${points[points.length - 1].x} ${baseline} L ${points[0].x} ${baseline} Z`;
  }, [pathD, points, chartHeight]);

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
        aria-label="Line chart"
      >
        {/* Grid lines */}
        {showGrid &&
          yTicks.map((tick, i) => {
            const y =
              PADDING.top + chartHeight - ((tick - minValue) / (maxValue - minValue)) * chartHeight;
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

        {/* X-axis labels */}
        {showLabels &&
          xTicks.map((tick, i) => (
            <text
              key={`x-label-${i}`}
              x={tick.x}
              y={height - PADDING.bottom + 20}
              textAnchor="middle"
              className="fill-gray-500 text-xs"
            >
              {xAxisFormatter(tick.label)}
            </text>
          ))}

        {/* Area fill */}
        {fillColor && <path d={areaD} fill={fillColor} />}

        {/* Line */}
        <path
          d={pathD}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {showDots &&
          points.map((p, i) => (
            <circle
              key={`dot-${i}`}
              cx={p.x}
              cy={p.y}
              r={4}
              fill={strokeColor}
              stroke="#fff"
              strokeWidth={2}
            >
              <title>{`${p.label}: ${p.value}`}</title>
            </circle>
          ))}
      </svg>
    </div>
  );
};

export default LineChart;
