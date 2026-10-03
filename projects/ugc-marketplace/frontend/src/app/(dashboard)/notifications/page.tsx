"use client";

import { Bell, CheckCheck, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { useNotifications } from "@/components/providers/NotificationProvider";
import { timeAgo } from "@/lib/utils";

export default function NotificationsPage() {
  const { notifications, markAsRead, markAllAsRead, deleteNotification, unreadCount } = useNotifications();

  const typeColors = { info: "default", success: "success", warning: "warning", error: "destructive" } as const;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="text-muted-foreground">{unreadCount} unread notifications</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={markAllAsRead}><CheckCheck className="mr-2 h-4 w-4" />Mark All Read</Button>
        </div>
      </div>
      {notifications.length === 0 ? (
        <EmptyState icon={Bell} title="No notifications" description="You're all caught up!" />
      ) : (
        <div className="space-y-2">
          {notifications.map((notification) => (
            <Card key={notification.id} className={!notification.read ? "border-primary/50" : ""}>
              <CardContent className="flex items-start justify-between p-4">
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 h-2 w-2 rounded-full ${notification.read ? "bg-muted" : "bg-primary"}`} />
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{notification.title}</p>
                      <Badge variant={typeColors[notification.type]}>{notification.type}</Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{notification.message}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{timeAgo(notification.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {!notification.read && (
                    <Button variant="ghost" size="icon" onClick={() => markAsRead(notification.id)}>
                      <CheckCheck className="h-4 w-4" />
                    </Button>
                  )}
                  <Button variant="ghost" size="icon" onClick={() => deleteNotification(notification.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
