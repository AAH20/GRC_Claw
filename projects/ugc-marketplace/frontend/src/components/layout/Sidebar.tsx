"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Users, FileText, ShoppingCart, ArrowLeftRight,
  BarChart3, Settings, Shield, Bell, LogOut, X, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "../providers/AuthProvider";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/creators", label: "Creators", icon: Users },
  { href: "/content", label: "Content", icon: FileText },
  { href: "/listings", label: "Listings", icon: ShoppingCart },
  { href: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/moderation", label: "Moderation", icon: Shield },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={onClose} />}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 h-full w-64 transform border-r bg-card transition-transform duration-200 ease-in-out lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center justify-between border-b px-6">
            <Link href="/dashboard" className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <span className="text-lg font-bold">UGC Marketplace</span>
            </Link>
            <button onClick={onClose} className="lg:hidden">
              <X className="h-5 w-5" />
            </button>
          </div>
          <nav className="flex-1 space-y-1 overflow-y-auto p-4">
            {navItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="border-t p-4">
            <button
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <LogOut className="h-5 w-5" />
              Sign Out
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
