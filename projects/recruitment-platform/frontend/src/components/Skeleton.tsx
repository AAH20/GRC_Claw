"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  variant = "text",
  width,
  height,
  className,
  ...props
}: SkeletonProps) {
  const styles: React.CSSProperties = {};
  if (width) styles.width = typeof width === "number" ? `${width}px` : width;
  if (height) styles.height = typeof height === "number" ? `${height}px` : height;

  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-gray-200 dark:bg-gray-700",
        variant === "circular" && "rounded-full",
        className
      )}
      style={styles}
      {...props}
    />
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4">
          <Skeleton variant="circular" width={40} height={40} />
          <div className="flex-1 space-y-2">
            <Skeleton width="40%" height={16} />
            <Skeleton width="60%" height={12} />
          </div>
          <Skeleton width={80} height={24} />
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4">
      <div className="flex items-center space-x-4">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="flex-1 space-y-2">
          <Skeleton width="50%" height={16} />
          <Skeleton width="30%" height={12} />
        </div>
      </div>
      <Skeleton width="100%" height={12} />
      <Skeleton width="80%" height={12} />
    </div>
  );
}
