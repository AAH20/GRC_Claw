"use client";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { formatNumber } from "@/lib/utils";

interface ContentPerformanceProps {
  data: { type: string; count: number; views: number }[];
  isLoading?: boolean;
}

export function ContentPerformance({ data, isLoading }: ContentPerformanceProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Content Performance</CardTitle></CardHeader>
        <CardContent><div className="h-48 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }
  const maxViews = Math.max(...data.map((d) => d.views), 1);
  return (
    <Card data-testid="content-performance">
      <CardHeader><CardTitle>Content Performance</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.map((item) => (
            <div key={item.type} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium capitalize">{item.type}</span>
                <span className="text-muted-foreground">{formatNumber(item.views)} views</span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div className="h-2 rounded-full bg-primary" style={{ width: `${(item.views / maxViews) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
