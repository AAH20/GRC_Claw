"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Avatar } from "@/components/Avatar";
import { useAuth } from "@/context/AuthContext";
import { cn, getInitials, formatRelativeTime } from "@/lib/utils";
import { Bell, Check, CheckCheck, Trash2, User, Briefcase, Calendar, FileText, Settings } from "lucide-react";

const mockNotifications = [
  { id: "1", title: "New application", message: "Sarah Johnson applied for Senior Frontend Developer", type: "info", read: false, createdAt: "2024-01-16T10:30:00Z", icon: User },
  { id: "2", title: "Interview reminder", message: "Interview with Michael Chen at 2:00 PM today", type: "warning", read: false, createdAt: "2024-01-16T08:00:00Z", icon: Calendar },
  { id: "3", title: "Job posted", message: "Backend Developer position is now live", type: "success", read: false, createdAt: "2024-01-15T14:00:00Z", icon: Briefcase },
  { id: "4", title: "Application update", message: "James Wilson accepted the offer", type: "success", read: true, createdAt: "2024-01-15T11:00:00Z", icon: FileText },
  { id: "5", title: "New message", message: "You have a new message from Emily Davis", type: "info", read: true, createdAt: "2024-01-14T16:00:00Z", icon: Bell },
  { id: "6", title: "Interview feedback", message: "Feedback received for Lisa Anderson", type: "info", read: true, createdAt: "2024-01-14T09:00:00Z", icon: Check },
];

const typeColors: Record<string, string> = {
  info: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
  success: "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400",
  warning: "bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400",
  error: "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400",
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState(mockNotifications);

  const markAsRead = (id: string) => {
    setNotifications(notifications.map((n) => n.id === id ? { ...n, read: true } : n));
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, read: true })));
  };

  const deleteNotification = (id: string) => {
    setNotifications(notifications.filter((n) => n.id !== id));
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Notifications</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {unreadCount > 0 ? `You have ${unreadCount} unread notification${unreadCount > 1 ? "s" : ""}` : "All caught up!"}
          </p>
        </div>
        {unreadCount > 0 && (
          <Button variant="outline" onClick={markAllAsRead} leftIcon={<CheckCheck className="h-4 w-4" />}>
            Mark All as Read
          </Button>
        )}
      </div>

      <Card padding="none">
        {notifications.length === 0 ? (
          <div className="py-12 text-center">
            <Bell className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">No notifications</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={cn(
                  "flex items-start gap-4 p-4 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50",
                  !notification.read && "bg-primary-50/50 dark:bg-primary-900/10"
                )}
              >
                <div className={cn("p-2 rounded-lg flex-shrink-0", typeColors[notification.type])}>
                  <notification.icon className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className={cn("text-sm", notification.read ? "font-medium text-gray-700 dark:text-gray-300" : "font-semibold text-gray-900 dark:text-gray-100")}>
                      {notification.title}
                    </h3>
                    {!notification.read && <span className="h-2 w-2 rounded-full bg-primary-500" />}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{notification.message}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{formatRelativeTime(notification.createdAt)}</p>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  {!notification.read && (
                    <Button variant="ghost" size="sm" onClick={() => markAsRead(notification.id)}>
                      <Check className="h-4 w-4" />
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" onClick={() => deleteNotification(notification.id)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
