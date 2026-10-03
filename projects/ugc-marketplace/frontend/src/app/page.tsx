"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";
import { useAuth } from "@/components/providers/AuthProvider";
import { PageSpinner } from "@/components/ui/Spinner";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      router.replace(isAuthenticated ? "/dashboard" : "/login");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Sparkles className="mx-auto h-12 w-12 text-primary animate-pulse" />
        <h1 className="mt-4 text-2xl font-bold">UGC Marketplace</h1>
        <PageSpinner />
      </div>
    </div>
  );
}
