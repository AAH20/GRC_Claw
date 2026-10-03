"use client";

import { TrendingUp, TrendingDown, type LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./Card";

interface StatCardProps {
  title: string;
  value: string;
  change?: number;
  icon: LucideIcon;
  description?: string;
}

export function StatCard({ title, value, change, icon: Icon, description }: StatCardProps) {
  const isPositive = (change ?? 0) >= 0;
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <div className="mt-1 flex items-center gap-1 text-sm">
            {isPositive ? <TrendingUp className="h-4 w-4 text-success" aria-hidden="true" /> : <TrendingDown className="h-4 w-4 text-destructive" aria-hidden="true" />}
            <span className={isPositive ? "text-success" : "text-destructive"}>{Math.abs(change)}%</span>
            {description && <span className="text-muted-foreground">{description}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
