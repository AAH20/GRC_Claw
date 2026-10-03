"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <div className="hidden flex-1 items-center justify-center bg-primary lg:flex">
        <div className="max-w-md text-center text-primary-foreground">
          <Sparkles className="mx-auto h-16 w-16 mb-6" />
          <h1 className="text-4xl font-bold mb-4">UGC Marketplace</h1>
          <p className="text-lg opacity-80">
            The premier platform for creators and brands to collaborate on authentic content.
          </p>
        </div>
      </div>
      <div className="flex flex-1 items-center justify-center p-6">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
