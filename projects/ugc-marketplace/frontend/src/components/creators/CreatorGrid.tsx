"use client";

import { CreatorCard } from "./CreatorCard";
import { CardSkeleton } from "../ui/Skeleton";
import { EmptyState } from "../ui/EmptyState";
import { Users } from "lucide-react";
import type { Creator } from "@/lib/types";

interface CreatorGridProps {
  creators: Creator[];
  isLoading?: boolean;
  onMessage?: (id: string) => void;
  onToggleFollow?: (id: string) => void;
}

export function CreatorGrid({ creators, isLoading, onMessage, onToggleFollow }: CreatorGridProps) {
  if (isLoading) {
    return (
      <div data-testid="creator-grid" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
    );
  }
  if (creators.length === 0) {
    return <EmptyState icon={Users} title="No creators found" description="Try adjusting your search or filters." />;
  }
  return (
    <div data-testid="creator-grid" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {creators.map((creator) => (
        <CreatorCard key={creator.id} creator={creator} onMessage={onMessage} onToggleFollow={onToggleFollow} />
      ))}
    </div>
  );
}
