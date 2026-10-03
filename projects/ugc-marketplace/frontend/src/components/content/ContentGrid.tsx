"use client";

import { ContentCard } from "./ContentCard";
import { CardSkeleton } from "../ui/Skeleton";
import { EmptyState } from "../ui/EmptyState";
import { FileText } from "lucide-react";
import type { Content } from "@/lib/types";

interface ContentGridProps {
  content: Content[];
  isLoading?: boolean;
  onView?: (id: string) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function ContentGrid({ content, isLoading, onView, onEdit, onDelete }: ContentGridProps) {
  if (isLoading) {
    return (
      <div data-testid="content-grid" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
    );
  }
  if (content.length === 0) {
    return <EmptyState icon={FileText} title="No content found" description="Try adjusting your search or filters." />;
  }
  return (
    <div data-testid="content-grid" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {content.map((item) => (
        <ContentCard key={item.id} content={item} onView={onView} onEdit={onEdit} onDelete={onDelete} />
      ))}
    </div>
  );
}
