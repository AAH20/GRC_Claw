'use client';

import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}

export default function StatCard({ title, value, change, changeLabel, icon, trend }: StatCardProps) {
  const trendColor = trend === 'up' ? 'text-green-600 dark:text-green-400' : trend === 'down' ? 'text-red-600 dark:text-red-400' : 'text-surface-500';
  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';

  return (
    <div className="rounded-xl border border-surface-200 bg-white p-6 dark:border-surface-700 dark:bg-surface-800">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-surface-500 dark:text-surface-400">{title}</p>
          <p className="mt-1 text-2xl font-bold text-surface-900 dark:text-white">{value}</p>
          {change !== undefined && (
            <p className={`mt-1 text-sm ${trendColor}`}>
              <span>{trendIcon} {Math.abs(change)}%</span>
              {changeLabel && <span className="ml-1 text-surface-400">{changeLabel}</span>}
            </p>
          )}
        </div>
        {icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
