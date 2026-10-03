"use client";

import { cn } from "@/lib/utils";

interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
}

export function ProgressBar({ value, max = 100, className, showLabel }: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  return (
    <div className={cn("space-y-1", className)}>
      <div className="h-2 w-full rounded-full bg-muted">
        <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${percentage}%` }} />
      </div>
      {showLabel && <p className="text-xs text-muted-foreground">{percentage.toFixed(0)}%</p>}
    </div>
  );
}
