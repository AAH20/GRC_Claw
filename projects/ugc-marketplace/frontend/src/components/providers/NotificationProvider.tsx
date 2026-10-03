"use client";

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";
import apiClient from "@/lib/api-client";
import type { Notification } from "@/lib/types";

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  deleteNotification: (id: string) => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.get<Notification[]>("/notifications");
      setNotifications(data);
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markAsRead = useCallback(async (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
    try {
      await apiClient.patch(`/notifications/${id}/read`);
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    try {
      await apiClient.patch("/notifications/read-all");
    } catch (error) {
      console.error("Failed to mark all notifications as read:", error);
    }
  }, []);

  const deleteNotification = useCallback(async (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    try {
      await apiClient.delete(`/notifications/${id}`);
    } catch (error) {
      console.error("Failed to delete notification:", error);
    }
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <NotificationContext.Provider
      value={{ notifications, unreadCount, isLoading, fetchNotifications, markAsRead, markAllAsRead, deleteNotification }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) throw new Error("useNotifications must be used within NotificationProvider");
  return context;
}
