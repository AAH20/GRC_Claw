"use client";

import React from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />
        <main id="main-content" className="flex-1 overflow-y-auto p-4 lg:p-6 scrollbar-thin" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
