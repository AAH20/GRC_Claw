import React from "react";

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
  outerRadius?: number;
  showLegend?: boolean;
  legendPosition?: "right" | "bottom";
  showLabels?: boolean;
  labelColor?: string;
  valueFormatter?: (value: number) => string;
  title?: string;
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
  "#f97316",
  "#6366f1",
];

export const PieChart: React.FC<PieChartProps> = ({
  data,
  width = 400,
  height = 300,
  innerRadius = 0,
  outerRadius,
  showLegend = true,
  legendPosition = "right",
  showLabels = true,
  labelColor = "#374151",
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

  const total = data.reduce((sum, d) => sum + d.value, 0) || 1;
  const computedOuterRadius =
    outerRadius || Math.min(width, height) / 2 - (showLegend && legendPosition === "right" ? 80 : 20);
  const centerX = showLegend && legendPosition === "right" ? width / 2 - 60 : width / 2;
  const centerY = showLegend && legendPosition === "bottom" ? height / 2 - 40 : height / 2;

  const getColor = (index: number, explicitColor?: string) =>
    explicitColor || DEFAULT_COLORS[index % DEFAULT_COLORS.length];

  const createArcPath = (
    cx: number,
    cy: number,
    rInner: number,
    rOuter: number,
    startAngle: number,
    endAngle: number
  ): string => {
    const startOuter = {
      x: cx + rOuter * Math.cos(startAngle),
      y: cy + rOuter * Math.sin(startAngle),
    };
    const endOuter = {
      x: cx + rOuter * Math.cos(endAngle),
      y: cy + rOuter * Math.sin(endAngle),
    };
    const startInner = {
      x: cx + rInner * Math.cos(endAngle),
      y: cy + rInner * Math.sin(endAngle),
    };
    const endInner = {
      x: cx + rInner * Math.cos(startAngle),
      y: cy + rInner * Math.sin(startAngle),
    };

    const largeArcFlag = endAngle - startAngle > Math.PI ? 1 : 0;

    if (rInner === 0) {
      return [
        `M ${cx} ${cy}`,
        `L ${startOuter.x} ${startOuter.y}`,
        `A ${rOuter} ${rOuter} 0 ${largeArcFlag} 1 ${endOuter.x} ${endOuter.y}`,
        "Z",
      ].join(" ");
    }

    return [
      `M ${startOuter.x} ${startOuter.y}`,
      `A ${rOuter} ${rOuter} 0 ${largeArcFlag} 1 ${endOuter.x} ${endOuter.y}`,
      `L ${startInner.x} ${startInner.y}`,
      `A ${rInner} ${rInner} 0 ${largeArcFlag} 0 ${endInner.x} ${endInner.y}`,
      "Z",
    ].join(" ");
  };

  let currentAngle = -Math.PI / 2; // Start at top

  const segments = data.map((d, i) => {
    const fraction = d.value / total;
    const sweepAngle = fraction * 2 * Math.PI;
    const startAngle = currentAngle;
    const endAngle = currentAngle + sweepAngle;
    currentAngle = endAngle;

    const midAngle = startAngle + sweepAngle / 2;
    const labelRadius = (computedOuterRadius + innerRadius) / 2;
    const labelX = centerX + labelRadius * Math.cos(midAngle);
    const labelY = centerY + labelRadius * Math.sin(midAngle);

    const percentage = Math.round(fraction * 100);

    return {
      path: createArcPath(
        centerX,
        centerY,
        innerRadius,
        computedOuterRadius,
        startAngle,
        endAngle
      ),
      color: getColor(i, d.color),
      label: d.label,
      value: d.value,
      percentage,
      labelX,
      labelY,
      midAngle,
    };
  });

  const isDonut = innerRadius > 0;

  return (
    <div className={`inline-block ${className}`}>
      {title && (
        <h3 className="mb-2 text-center text-sm font-semibold text-gray-700">
          {title}
        </h3>
      )}
      <div className="flex" style={{ flexDirection: legendPosition === "bottom" ? "column" : "row" }}>
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={title || "Pie chart"}
          className="flex-shrink-0"
        >
          {/* Segments */}
          {segments.map((seg, i) => (
            <path
              key={`segment-${i}`}
              d={seg.path}
              fill={seg.color}
              stroke="#fff"
              strokeWidth={2}
            >
              <title>{`${seg.label}: ${valueFormatter(seg.value)} (${seg.percentage}%)`}</title>
            </path>
          ))}

          {/* Labels on segments */}
          {showLabels &&
            segments.map((seg, i) => (
              <text
                key={`label-${i}`}
                x={seg.labelX}
                y={seg.labelY}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={11}
                fill={labelColor}
                fontWeight={500}
              >
                {`${seg.percentage}%`}
              </text>
            ))}

          {/* Donut center text */}
          {isDonut && (
            <text
              x={centerX}
              y={centerY}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={14}
              fontWeight={600}
              fill={labelColor}
            >
              {valueFormatter(total)}
            </text>
          )}
        </svg>

        {/* Legend */}
        {showLegend && (
          <div
            className={
              legendPosition === "right"
                ? "ml-4 flex flex-col justify-center gap-2"
                : "mt-4 flex flex-wrap justify-center gap-3"
            }
          >
            {segments.map((seg, i) => (
              <div key={`legend-${i}`} className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-sm"
                  style={{ backgroundColor: seg.color }}
                />
                <span className="text-xs text-gray-600">
                  {seg.label}
                  <span className="ml-1 text-gray-400">
                    ({valueFormatter(seg.value)} · {seg.percentage}%)
                  </span>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PieChart;
