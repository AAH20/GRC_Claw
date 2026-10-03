"use client";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { formatCurrency } from "@/lib/utils";

interface TransactionChartProps {
  data: { month: string; revenue: number }[];
  isLoading?: boolean;
}

export function TransactionChart({ data, isLoading }: TransactionChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Revenue Overview</CardTitle></CardHeader>
        <CardContent><div className="h-64 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  const maxRevenue = Math.max(...data.map((d) => d.revenue), 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex h-64 items-end gap-2">
          {data.map((item) => (
            <div key={item.month} className="flex flex-1 flex-col items-center gap-2">
              <div className="relative w-full flex-1 flex items-end">
                <div
                  className="w-full rounded-t-md bg-primary/80 transition-all hover:bg-primary"
                  style={{ height: `${(item.revenue / maxRevenue) * 100}%` }}
                  title={`${item.month}: ${formatCurrency(item.revenue)}`}
                />
              </div>
              <span className="text-xs text-muted-foreground">{item.month}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Total Revenue</span>
          <span className="font-semibold">{formatCurrency(data.reduce((sum, d) => sum + d.revenue, 0))}</span>
        </div>
      </CardContent>
    </Card>
  );
}
