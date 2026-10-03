"use client";

import { AlertTriangle, CheckCircle, XCircle, Clock, MoreVertical, User, FileText, ShoppingCart, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Avatar } from "../ui/Avatar";
import { timeAgo } from "@/lib/utils";
import type { ModerationItem } from "@/lib/types";

interface ModerationQueueProps {
  items: ModerationItem[];
  isLoading?: boolean;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  onEscalate?: (id: string) => void;
}

export function ModerationQueue({ items, isLoading, onApprove, onReject, onEscalate }: ModerationQueueProps) {
  const priorityColors = { low: "secondary", medium: "warning", high: "destructive", critical: "destructive" } as const;
  const statusColors = { pending: "warning", approved: "success", rejected: "destructive", escalated: "default" } as const;
  const typeIcons = { content: FileText, creator: User, listing: ShoppingCart, dispute: AlertCircle };

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Moderation Queue</CardTitle></CardHeader>
        <CardContent><div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />)}</div></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Moderation Queue</CardTitle>
          <Badge variant="warning">{items.filter((i) => i.status === "pending").length} pending</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {items.map((item) => {
            const Icon = typeIcons[item.type];
            return (
              <div key={item.id} className="rounded-lg border p-4 hover:bg-accent/50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{item.target_name}</p>
                        <Badge variant={priorityColors[item.priority]}>{item.priority}</Badge>
                        <Badge variant={statusColors[item.status]}>{item.status}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{item.reason}</p>
                      <p className="mt-1 text-xs text-muted-foreground">Reported by {item.reported_by} · {timeAgo(item.created_at)}</p>
                    </div>
                  </div>
                  {item.status === "pending" && (
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" onClick={() => onApprove?.(item.id)} className="text-green-600 hover:text-green-700">
                        <CheckCircle className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => onReject?.(item.id)} className="text-red-600 hover:text-red-700">
                        <XCircle className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => onEscalate?.(item.id)}>
                        <AlertTriangle className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
