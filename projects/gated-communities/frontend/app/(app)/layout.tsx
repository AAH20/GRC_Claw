'use client';

import React from 'react';
import { useAuth } from '@/context/AuthContext';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-900">
      <Sidebar />
      <div className="lg:pl-64">
        <Header />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
