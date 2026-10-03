"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { Avatar } from "./Avatar";
import { Badge } from "./Badge";
import { cn, getInitials } from "@/lib/utils";
import { Bell, Search, Sun, Moon, User, Settings, LogOut, ChevronDown } from "lucide-react";

export function Header() {
  const { user, logout } = useAuth();
  const { resolvedTheme, toggle } = useTheme();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between px-4 lg:px-6 py-3">
        <div className="flex items-center gap-4 flex-1">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search candidates, jobs..."
              className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggle}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 transition-colors"
          >
            {resolvedTheme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>

          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 transition-colors relative"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full" />
            </button>
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-2 animate-fade-in">
                <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Notifications</h3>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {[
                    { title: "New application", message: "John applied for Frontend Developer", time: "2m ago" },
                    { title: "Interview reminder", message: "Interview with Sarah at 3:00 PM", time: "1h ago" },
                    { title: "Job posted", message: "Backend Developer position is live", time: "3h ago" },
                  ].map((n, i) => (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{n.title}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{n.message}</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{n.time}</p>
                    </div>
                  ))}
                </div>
                <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
                  <Link href="/notifications" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
                    View all notifications
                  </Link>
                </div>
              </div>
            )}
          </div>

          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <Avatar alt={user?.name || "User"} fallback={getInitials(user?.name || "U")} size="sm" />
              <div className="hidden sm:block text-left">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{user?.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{user?.role}</p>
              </div>
              <ChevronDown className="h-4 w-4 text-gray-400" />
            </button>
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-2 animate-fade-in">
                <Link href="/profile" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <User className="h-4 w-4" /> Profile
                </Link>
                <Link href="/settings" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <Settings className="h-4 w-4" /> Settings
                </Link>
                <hr className="my-1 border-gray-200 dark:border-gray-700" />
                <button onClick={logout} className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 w-full">
                  <LogOut className="h-4 w-4" /> Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
