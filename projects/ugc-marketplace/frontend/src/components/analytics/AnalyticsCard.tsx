"use client";

import { TrendingUp, TrendingDown, type LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

interface AnalyticsCardProps {
  title: string;
  value: string;
  change: number;
  icon: LucideIcon;
  suffix?: string;
}

export function AnalyticsCard({ title, value, change, icon: Icon, suffix }: AnalyticsCardProps) {
  const isPositive = change >= 0;
  return (
    <Card data-testid="analytics-card">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}{suffix && <span className="text-sm font-normal text-muted-foreground ml-1">{suffix}</span>}</div>
        <div className="mt-1 flex items-center gap-1 text-sm">
          {isPositive ? <TrendingUp className="h-4 w-4 text-success" aria-hidden="true" /> : <TrendingDown className="h-4 w-4 text-destructive" aria-hidden="true" />}
          <span className={isPositive ? "text-success" : "text-destructive"}>{Math.abs(change)}%</span>
          <span className="text-muted-foreground">vs last month</span>
        </div>
      </CardContent>
    </Card>
  );
}
