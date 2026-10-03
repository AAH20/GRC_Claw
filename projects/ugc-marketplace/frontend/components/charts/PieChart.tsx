'use client';

import React, { useMemo, useState } from 'react';

export interface PieChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface PieChartProps {
  data: PieChartDataPoint[];
  width?: number;
  height?: number;
  innerRadius?: number;
  colors?: string[];
  showLabels?: boolean;
  showLegend?: boolean;
  showPercentages?: boolean;
  className?: string;
  labelFormatter?: (label: string, value: number, percentage: number) => string;
}

const DEFAULT_WIDTH = 400;
const DEFAULT_HEIGHT = 300;
const DEFAULT_COLORS = [
  '#3b82f6',
  '#ef4444',
  '#10b981',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
  '#84cc16',
  '#f97316',
  '#6366f1',
];

export const PieChart: React.FC<PieChartProps> = ({
  data,
  width = DEFAULT_WIDTH,
  height = DEFAULT_HEIGHT,
  innerRadius = 0,
  colors = DEFAULT_COLORS,
  showLabels = true,
  showLegend = true,
  showPercentages = true,
  className = '',
  labelFormatter = (label, _value, percentage) => `${label}: ${percentage.toFixed(1)}%`,
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const { slices, total } = useMemo(() => {
    const totalValue = data.reduce((sum, d) => sum + d.value, 0);
    if (totalValue === 0) return { slices: [], total: 0 };

    let currentAngle = -Math.PI / 2; // Start at top
    const computedSlices = data.map((d, i) => {
      const fraction = d.value / totalValue;
      const angle = fraction * 2 * Math.PI;
      const startAngle = currentAngle;
      const endAngle = currentAngle + angle;
      currentAngle = endAngle;

      const midAngle = (startAngle + endAngle) / 2;
      const outerR = Math.min(width, height) / 2 - 10;
      const innerR = innerRadius;
      const hasDonut = innerR > 0;

      const x1Outer = outerR * Math.cos(startAngle);
      const y1Outer = outerR * Math.sin(startAngle);
      const x2Outer = outerR * Math.cos(endAngle);
      const y2Outer = outerR * Math.sin(endAngle);

      let pathD: string;
      if (hasDonut) {
        const x1Inner = innerR * Math.cos(endAngle);
        const y1Inner = innerR * Math.sin(endAngle);
        const x2Inner = innerR * Math.cos(startAngle);
        const y2Inner = innerR * Math.sin(startAngle);
        const largeArc = angle > Math.PI ? 1 : 0;

        pathD = [
          `M ${x1Outer} ${y1Outer}`,
          `A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2Outer} ${y2Outer}`,
          `L ${x1Inner} ${y1Inner}`,
          `A ${innerR} ${innerR} 0 ${largeArc} 0 ${x2Inner} ${y2Inner}`,
          'Z',
        ].join(' ');
      } else {
        const largeArc = angle > Math.PI ? 1 : 0;
        pathD = [
          `M 0 0`,
          `L ${x1Outer} ${y1Outer}`,
          `A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2Outer} ${y2Outer}`,
          'Z',
        ].join(' ');
      }

      const labelR = hasDonut ? (outerR + innerR) / 2 : outerR * 0.7;
      const labelX = labelR * Math.cos(midAngle);
      const labelY = labelR * Math.sin(midAngle);

      return {
        ...d,
        color: d.color || colors[i % colors.length],
        pathD,
        midAngle,
        percentage: fraction * 100,
        labelX,
        labelY,
        startAngle,
        endAngle,
      };
    });

    return { slices: computedSlices, total: totalValue };
  }, [data, width, height, innerRadius, colors]);

  if (data.length === 0 || total === 0) {
    return (
      <div
        className={`flex items-center justify-center text-gray-400 ${className}`}
        style={{ width, height }}
      >
        No data available
      </div>
    );
  }

  const centerX = width / 2;
  const centerY = height / 2;
  const legendWidth = showLegend ? 140 : 0;
  const chartCenterX = (width - legendWidth) / 2;

  return (
    <div className={`inline-block ${className}`}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="overflow-visible"
        role="img"
        aria-label="Pie chart"
      >
        {/* Slices */}
        <g transform={`translate(${chartCenterX}, ${centerY})`}>
          {slices.map((slice, i) => (
            <path
              key={`slice-${i}`}
              d={slice.pathD}
              fill={slice.color}
              stroke="#fff"
              strokeWidth={2}
              opacity={hoveredIndex === null || hoveredIndex === i ? 1 : 0.6}
              className="transition-opacity duration-150 cursor-pointer"
              onMouseEnter={() => setHoveredIndex(i)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <title>{`${slice.label}: ${slice.value} (${slice.percentage.toFixed(1)}%)`}</title>
            </path>
          ))}

          {/* Labels on slices */}
          {showLabels &&
            !showPercentages &&
            slices.map((slice, i) => (
              <text
                key={`label-${i}`}
                x={slice.labelX}
                y={slice.labelY}
                textAnchor="middle"
                dominantBaseline="middle"
                className="fill-white text-xs font-medium pointer-events-none"
              >
                {slice.label}
              </text>
            ))}

          {/* Percentage labels on slices */}
          {showPercentages &&
            slices.map((slice, i) => (
              <text
                key={`pct-${i}`}
                x={slice.labelX}
                y={slice.labelY}
                textAnchor="middle"
                dominantBaseline="middle"
                className="fill-white text-xs font-medium pointer-events-none"
              >
                {slice.percentage.toFixed(1)}%
              </text>
            ))}
        </g>

        {/* Legend */}
        {showLegend && (
          <g transform={`translate(${width - legendWidth + 10}, ${centerY - (slices.length * 24) / 2})`}>
            {slices.map((slice, i) => (
              <g
                key={`legend-${i}`}
                transform={`translate(0, ${i * 24})`}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredIndex(i)}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                <rect
                  x={0}
                  y={0}
                  width={14}
                  height={14}
                  rx={2}
                  fill={slice.color}
                  opacity={hoveredIndex === null || hoveredIndex === i ? 1 : 0.6}
                />
                <text
                  x={20}
                  y={11}
                  className="fill-gray-600 text-xs"
                >
                  {labelFormatter(slice.label, slice.value, slice.percentage)}
                </text>
              </g>
            ))}
          </g>
        )}
      </svg>
    </div>
  );
};

export default PieChart;
