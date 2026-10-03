"use client";

import { useState } from "react";
import { Menu, Search, Bell, Moon, Sun, User } from "lucide-react";
import { useTheme } from "../providers/ThemeProvider";
import { useNotifications } from "../providers/NotificationProvider";
import { useAuth } from "../providers/AuthProvider";
import { Avatar } from "../ui/Avatar";
import { Input } from "../ui/Input";
import Link from "next/link";

export function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const { resolvedTheme, toggleTheme } = useTheme();
  const { unreadCount } = useNotifications();
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-card px-4 lg:px-6">
      <div className="flex items-center gap-4">
        <button onClick={onMenuClick} className="lg:hidden" aria-label="Open menu">
          <Menu className="h-6 w-6" aria-hidden="true" />
        </button>
        <div className="hidden md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64 pl-9"
            />
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="flex h-10 w-10 items-center justify-center rounded-md text-muted-foreground hover:bg-accent"
          aria-label={resolvedTheme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {resolvedTheme === "dark" ? <Sun className="h-5 w-5" aria-hidden="true" /> : <Moon className="h-5 w-5" aria-hidden="true" />}
        </button>
        <Link href="/notifications" className="relative flex h-10 w-10 items-center justify-center rounded-md text-muted-foreground hover:bg-accent" aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ""}`}>
          <Bell className="h-5 w-5" aria-hidden="true" />
          {unreadCount > 0 && (
            <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-white">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Link>
        <Link href="/profile" className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-accent">
          <Avatar src={user?.avatar} alt={user?.name} size="sm" />
          <span className="hidden text-sm font-medium md:block">{user?.name}</span>
        </Link>
      </div>
    </header>
  );
}
