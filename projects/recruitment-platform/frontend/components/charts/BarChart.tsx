import React from "react";

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
  gridColor?: string;
  axisColor?: string;
  labelColor?: string;
  valueColor?: string;
  valueFormatter?: (value: number) => string;
  title?: string;
  horizontal?: boolean;
  className?: string;
}

const DEFAULT_VALUE_FORMATTER = (v: number) => v.toLocaleString();
const DEFAULT_COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#84cc16",
];

export const BarChart: React.FC<BarChartProps> = ({
  data,
  width = 600,
  height = 300,
  barColor = "#3b82f6",
  barRadius = 4,
  showGrid = true,
  gridColor = "#e5e7eb",
  axisColor = "#9ca3af",
  labelColor = "#6b7280",
  valueColor = "#374151",
  valueFormatter = DEFAULT_VALUE_FORMATTER,
  title,
  horizontal = false,
  className = "",
}) => {
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

  const padding = { top: 20, right: 30, bottom: 40, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const maxValue = Math.max(...data.map((d) => d.value));
  const valueRange = maxValue || 1;

  const gridLines = 5;
  const gridValues = Array.from({ length: gridLines }, (_, i) => {
    const ratio = i / (gridLines - 1);
    return ratio * valueRange;
  });

  const getBarColor = (index: number, explicitColor?: string) =>
    explicitColor || barColor || DEFAULT_COLORS[index % DEFAULT_COLORS.length];

  if (horizontal) {
    const barHeight = chartHeight / data.length;
    const barGap = barHeight * 0.2;
    const actualBarHeight = barHeight - barGap;

    return (
      <div className={`inline-block ${className}`}>
        {title && (
          <h3 className="mb-2 text-center text-sm font-semibold text-gray-700">
            {title}
          </h3>
        )}
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={title || "Horizontal bar chart"}
        >
          {/* Grid lines */}
          {showGrid &&
            gridValues.map((val, i) => {
              const x = padding.left + (val / valueRange) * chartWidth;
              return (
                <g key={`grid-${i}`}>
                  <line
                    x1={x}
                    y1={padding.top}
                    x2={x}
                    y2={height - padding.bottom}
                    stroke={gridColor}
                    strokeDasharray="4 4"
                  />
                  <text
                    x={x}
                    y={height - padding.bottom + 18}
                    textAnchor="middle"
                    fontSize={11}
                    fill={labelColor}
                  >
                    {valueFormatter(Math.round(val * 100) / 100)}
                  </text>
                </g>
              );
            })}

          {/* Axes */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left}
            y2={height - padding.bottom}
            stroke={axisColor}
            strokeWidth={1}
          />
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke={axisColor}
            strokeWidth={1}
          />

          {/* Bars */}
          {data.map((d, i) => {
            const barWidth = (d.value / valueRange) * chartWidth;
            const y = padding.top + i * barHeight + barGap / 2;
            return (
              <g key={`bar-${i}`}>
                <rect
                  x={padding.left}
                  y={y}
                  width={barWidth}
                  height={actualBarHeight}
                  fill={getBarColor(i, d.color)}
                  rx={barRadius}
                  ry={barRadius}
                >
                  <title>{`${d.label}: ${valueFormatter(d.value)}`}</title>
                </rect>
                <text
                  x={padding.left - 8}
                  y={y + actualBarHeight / 2 + 4}
                  textAnchor="end"
                  fontSize={11}
                  fill={labelColor}
                >
                  {d.label}
                </text>
                <text
                  x={padding.left + barWidth + 6}
                  y={y + actualBarHeight / 2 + 4}
                  fontSize={11}
                  fill={valueColor}
                >
                  {valueFormatter(d.value)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    );
  }

  // Vertical bar chart
  const barWidth = chartWidth / data.length;
  const barGap = barWidth * 0.2;
  const actualBarWidth = barWidth - barGap;

  return (
    <div className={`inline-block ${className}`}>
      {title && (
        <h3 className="mb-2 text-center text-sm font-semibold text-gray-700">
          {title}
        </h3>
      )}
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={title || "Bar chart"}
      >
        {/* Grid lines */}
        {showGrid &&
          gridValues.map((val, i) => {
            const y =
              padding.top + chartHeight - (val / valueRange) * chartHeight;
            return (
              <g key={`grid-${i}`}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke={gridColor}
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize={11}
                  fill={labelColor}
                >
                  {valueFormatter(Math.round(val * 100) / 100)}
                </text>
              </g>
            );
          })}

        {/* Axes */}
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
          stroke={axisColor}
          strokeWidth={1}
        />
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
          stroke={axisColor}
          strokeWidth={1}
        />

        {/* Bars */}
        {data.map((d, i) => {
          const barHeight = (d.value / valueRange) * chartHeight;
          const x = padding.left + i * barWidth + barGap / 2;
          const y = padding.top + chartHeight - barHeight;
          return (
            <g key={`bar-${i}`}>
              <rect
                x={x}
                y={y}
                width={actualBarWidth}
                height={barHeight}
                fill={getBarColor(i, d.color)}
                rx={barRadius}
                ry={barRadius}
              >
                <title>{`${d.label}: ${valueFormatter(d.value)}`}</title>
              </rect>
              <text
                x={x + actualBarWidth / 2}
                y={height - padding.bottom + 18}
                textAnchor="middle"
                fontSize={11}
                fill={labelColor}
              >
                {d.label}
              </text>
              <text
                x={x + actualBarWidth / 2}
                y={y - 6}
                textAnchor="middle"
                fontSize={11}
                fill={valueColor}
              >
                {valueFormatter(d.value)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default BarChart;
