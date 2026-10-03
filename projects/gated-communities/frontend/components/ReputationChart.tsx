'use client';

import React, { useMemo } from 'react';
import type { DataPoint, TierDistribution } from '@/lib/types';

interface ReputationChartProps {
  data: DataPoint[];
  tierDistribution?: TierDistribution[];
  title?: string;
  isLoading?: boolean;
  showLegend?: boolean;
  height?: number;
}

export default function ReputationChart({
  data,
  tierDistribution,
  title = 'Reputation & Growth',
  isLoading,
  showLegend = true,
  height = 300,
}: ReputationChartProps) {
  const chartData = useMemo(() => {
    if (data.length === 0) return null;

    const maxValue = Math.max(...data.map((d) => d.value));
    const minValue = Math.min(...data.map((d) => d.value));
    const range = maxValue - minValue || 1;

    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = 100 - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const points = data.map((d, i) => ({
      x: padding.left + (i / (data.length - 1)) * chartWidth,
      y: padding.top + chartHeight - ((d.value - minValue) / range) * chartHeight,
      ...d,
    }));

    const pathD = points
      .map((p, i) => {
        if (i === 0) return `M ${p.x} ${p.y}`;
        const prev = points[i - 1];
        const cpx1 = prev.x + (p.x - prev.x) / 3;
        const cpx2 = prev.x + (2 * (p.x - prev.x)) / 3;
        return `C ${cpx1} ${prev.y}, ${cpx2} ${p.y}, ${p.x} ${p.y}`;
      })
      .join(' ');

    const areaD = `${pathD} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`;

    const yTicks = Array.from({ length: 5 }, (_, i) => {
      const value = minValue + (range / 4) * i;
      const y = padding.top + chartHeight - (i / 4) * chartHeight;
      return { value: Math.round(value), y };
    });

    const xTicks = points.filter((_, i) => i % Math.ceil(points.length / 6) === 0);

    return { points, pathD, areaD, yTicks, xTicks, maxValue, minValue };
  }, [data, height]);

  const pieData = useMemo(() => {
    if (!tierDistribution || tierDistribution.length === 0) return null;
    const total = tierDistribution.reduce((sum, t) => sum + t.count, 0);
    let cumulativePercent = 0;

    return tierDistribution.map((tier) => {
      const percent = (tier.count / total) * 100;
      const startAngle = (cumulativePercent / 100) * 360;
      cumulativePercent += percent;
      const endAngle = (cumulativePercent / 100) * 360;
      return { ...tier, percent, startAngle, endAngle };
    });
  }, [tierDistribution]);

  if (isLoading) {
    return (
      <div className="animate-pulse rounded-xl border border-surface-200 bg-white p-6 dark:border-surface-700 dark:bg-surface-800">
        <div className="mb-4 h-5 w-1/3 rounded bg-surface-200 dark:bg-surface-700" />
        <div className="rounded bg-surface-200 dark:bg-surface-700" style={{ height }} />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-surface-200 bg-white p-6 dark:border-surface-700 dark:bg-surface-800">
      <h3 className="mb-4 font-semibold text-surface-900 dark:text-white">{title}</h3>

      {data.length === 0 && !pieData ? (
        <div className="flex items-center justify-center text-surface-500 dark:text-surface-400" style={{ height }}>
          <p>No data available</p>
        </div>
      ) : (
        <div className="flex flex-col gap-6 lg:flex-row">
          {chartData && (
            <div className="flex-1">
              <svg viewBox={`0 0 100 ${height}`} className="w-full" preserveAspectRatio="none" style={{ height }}>
                <defs>
                  <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {chartData.yTicks.map((tick, i) => (
                  <g key={i}>
                    <line
                      x1={50}
                      y1={tick.y}
                      x2={90}
                      y2={tick.y}
                      stroke="currentColor"
                      strokeWidth="0.2"
                      className="text-surface-200 dark:text-surface-700"
                    />
                    <text x={45} y={tick.y + 1} textAnchor="end" fontSize="3" className="fill-surface-400">
                      {tick.value.toLocaleString()}
                    </text>
                  </g>
                ))}

                <path d={chartData.areaD} fill="url(#areaGradient)" />
                <path d={chartData.pathD} fill="none" stroke="#3b82f6" strokeWidth="0.8" />

                {chartData.points.map((point, i) => (
                  <circle key={i} cx={point.x} cy={point.y} r="1" fill="#3b82f6" className="hover:r-2">
                    <title>{`${point.label || point.date}: ${point.value.toLocaleString()}`}</title>
                  </circle>
                ))}

                {chartData.xTicks.map((tick, i) => (
                  <text
                    key={i}
                    x={tick.x}
                    y={height - 5}
                    textAnchor="middle"
                    fontSize="3"
                    className="fill-surface-400"
                  >
                    {tick.label || tick.date}
                  </text>
                ))}
              </svg>
            </div>
          )}

          {pieData && showLegend && (
            <div className="w-full lg:w-48">
              <h4 className="mb-3 text-sm font-medium text-surface-700 dark:text-surface-300">Tier Distribution</h4>
              <div className="space-y-2">
                {pieData.map((tier) => (
                  <div key={tier.tierId} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full" style={{ backgroundColor: tier.color }} />
                      <span className="text-surface-600 dark:text-surface-300">{tier.tierName}</span>
                    </div>
                    <span className="font-medium text-surface-900 dark:text-white">{tier.percent.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
