"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { DashboardLayout } from "@/components/DashboardLayout";

export function AuthLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <DashboardLayout>{children}</DashboardLayout>;
}
