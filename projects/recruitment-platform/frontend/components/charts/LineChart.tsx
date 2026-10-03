import React from "react";

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
  fillOpacity?: number;
  showDots?: boolean;
  dotRadius?: number;
  showGrid?: boolean;
  gridColor?: string;
  axisColor?: string;
  labelColor?: string;
  valueFormatter?: (value: number) => string;
  title?: string;
  className?: string;
}

const DEFAULT_VALUE_FORMATTER = (v: number) => v.toLocaleString();

export const LineChart: React.FC<LineChartProps> = ({
  data,
  width = 600,
  height = 300,
  strokeColor = "#3b82f6",
  strokeWidth = 2,
  fillColor = "#3b82f6",
  fillOpacity = 0.1,
  showDots = true,
  dotRadius = 4,
  showGrid = true,
  gridColor = "#e5e7eb",
  axisColor = "#9ca3af",
  labelColor = "#6b7280",
  valueFormatter = DEFAULT_VALUE_FORMATTER,
  title,
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
  const minValue = Math.min(...data.map((d) => d.value));
  const valueRange = maxValue - minValue || 1;

  const xStep = chartWidth / Math.max(data.length - 1, 1);

  const getX = (index: number) => padding.left + index * xStep;
  const getY = (value: number) =>
    padding.top + chartHeight - ((value - minValue) / valueRange) * chartHeight;

  const linePath = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(d.value)}`)
    .join(" ");

  const areaPath = `${linePath} L ${getX(data.length - 1)} ${padding.top + chartHeight} L ${getX(0)} ${padding.top + chartHeight} Z`;

  const gridLines = 5;
  const gridValues = Array.from({ length: gridLines }, (_, i) => {
    const ratio = i / (gridLines - 1);
    return minValue + ratio * valueRange;
  });

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
        aria-label={title || "Line chart"}
      >
        {/* Grid lines */}
        {showGrid &&
          gridValues.map((val, i) => {
            const y = getY(val);
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

        {/* Area fill */}
        <path d={areaPath} fill={fillColor} fillOpacity={fillOpacity} />

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {showDots &&
          data.map((d, i) => (
            <circle
              key={`dot-${i}`}
              cx={getX(i)}
              cy={getY(d.value)}
              r={dotRadius}
              fill={strokeColor}
              stroke="#fff"
              strokeWidth={2}
            >
              <title>{`${d.label}: ${valueFormatter(d.value)}`}</title>
            </circle>
          ))}

        {/* X-axis labels */}
        {data.map((d, i) => (
          <text
            key={`label-${i}`}
            x={getX(i)}
            y={height - padding.bottom + 18}
            textAnchor="middle"
            fontSize={11}
            fill={labelColor}
          >
            {d.label}
          </text>
        ))}
      </svg>
    </div>
  );
};

export default LineChart;
