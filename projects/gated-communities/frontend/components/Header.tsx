'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';

export default function Header() {
  const pathname = usePathname();
  const { user } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();

  const pageTitle = pathname.split('/')[1]?.charAt(0).toUpperCase() + pathname.split('/')[1]?.slice(1) || 'Dashboard';

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-surface-200 bg-white/80 px-6 backdrop-blur-sm dark:border-surface-700 dark:bg-surface-800/80">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-surface-900 dark:text-white">{pageTitle}</h1>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-surface-500 hover:bg-surface-100 hover:text-surface-700 dark:text-surface-400 dark:hover:bg-surface-700 dark:hover:text-surface-200"
          aria-label="Toggle theme"
        >
          {resolvedTheme === 'dark' ? (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>
        <Link
          href="/settings"
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-surface-600 hover:bg-surface-100 dark:text-surface-300 dark:hover:bg-surface-700"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <span className="hidden sm:inline">{user?.name || 'User'}</span>
        </Link>
      </div>
    </header>
  );
}
