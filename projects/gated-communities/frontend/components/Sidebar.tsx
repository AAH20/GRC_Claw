'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    href: '/dashboard',
    label: 'Dashboard',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    href: '/communities',
    label: 'Communities',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    href: '/tiers',
    label: 'Tiers',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
      </svg>
    ),
  },
  {
    href: '/members',
    label: 'Members',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
  },
  {
    href: '/moderation',
    label: 'Moderation',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    href: '/analytics',
    label: 'Analytics',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    href: '/settings',
    label: 'Settings',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { resolvedTheme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const isActive = (href: string) => pathname.startsWith(href);

  return (
    <>
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Mobile toggle */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="fixed left-4 top-4 z-50 rounded-lg bg-white p-2 shadow-lg dark:bg-surface-800 lg:hidden"
        aria-label="Toggle sidebar"
      >
        <svg className="h-6 w-6 text-surface-700 dark:text-surface-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-40 h-full w-64 transform border-r border-surface-200 bg-white transition-transform dark:border-surface-700 dark:bg-surface-800 lg:translate-x-0 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-3 border-b border-surface-200 px-6 dark:border-surface-700">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white font-bold text-sm">
              GC
            </div>
            <span className="font-semibold text-surface-900 dark:text-white">Gated Communities</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 overflow-y-auto p-4">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive(item.href)
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                    : 'text-surface-600 hover:bg-surface-50 hover:text-surface-900 dark:text-surface-300 dark:hover:bg-surface-700 dark:hover:text-white'
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Bottom section */}
          <div className="border-t border-surface-200 p-4 dark:border-surface-700">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="truncate text-sm font-medium text-surface-900 dark:text-white">{user?.name || 'User'}</p>
                <p className="truncate text-xs text-surface-500 dark:text-surface-400">{user?.email || ''}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={toggleTheme}
                className="flex-1 rounded-lg border border-surface-300 px-3 py-2 text-sm text-surface-700 hover:bg-surface-50 dark:border-surface-600 dark:text-surface-300 dark:hover:bg-surface-700"
                aria-label="Toggle theme"
              >
                {resolvedTheme === 'dark' ? '☀️' : '🌙'}
              </button>
              <button
                onClick={logout}
                className="flex-1 rounded-lg border border-surface-300 px-3 py-2 text-sm text-surface-700 hover:bg-surface-50 dark:border-surface-600 dark:text-surface-300 dark:hover:bg-surface-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
