"use client";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Avatar } from "../ui/Avatar";
import { formatCurrency } from "@/lib/utils";

interface TopCreatorsProps {
  creators: { id: string; name: string; earnings: number }[];
  isLoading?: boolean;
}

export function TopCreators({ creators, isLoading }: TopCreatorsProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Top Creators</CardTitle></CardHeader>
        <CardContent><div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-10 animate-pulse rounded-lg bg-muted" />)}</div></CardContent>
      </Card>
    );
  }
  return (
    <Card data-testid="top-creators">
      <CardHeader><CardTitle>Top Creators</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-3">
          {creators.map((creator, index) => (
            <div key={creator.id} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">{index + 1}</span>
                <Avatar alt={creator.name} size="sm" />
                <span className="text-sm font-medium">{creator.name}</span>
              </div>
              <span className="text-sm font-semibold">{formatCurrency(creator.earnings)}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
