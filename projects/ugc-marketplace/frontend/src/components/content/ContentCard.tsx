"use client";

import { Heart, MessageCircle, Share2, Eye, DollarSign, MoreVertical, Play } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Avatar } from "../ui/Avatar";
import { formatNumber, formatCurrency, timeAgo } from "@/lib/utils";
import type { Content } from "@/lib/types";

interface ContentCardProps {
  content: Content;
  onView?: (id: string) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function ContentCard({ content, onView, onEdit, onDelete }: ContentCardProps) {
  const statusColors = {
    draft: "secondary",
    pending_review: "warning",
    approved: "success",
    rejected: "destructive",
    published: "default",
  } as const;

  const typeIcons = { video: Play, image: Eye, story: Eye, reel: Play, blog: Eye };

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md">
      <div className="relative aspect-video bg-muted">
        {content.thumbnail ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={content.thumbnail} alt={content.title} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center">
            {(() => { const Icon = typeIcons[content.type]; return <Icon className="h-12 w-12 text-muted-foreground" />; })()}
          </div>
        )}
        <div className="absolute left-2 top-2">
          <Badge variant={statusColors[content.status]}>{content.status.replace("_", " ")}</Badge>
        </div>
        {content.monetization_enabled && (
          <div className="absolute right-2 top-2">
            <Badge variant="default" className="bg-green-600 text-white"><DollarSign className="h-3 w-3 mr-1" />Monetized</Badge>
          </div>
        )}
      </div>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Avatar src={content.creator_avatar} alt={content.creator_name} size="sm" />
            <div>
              <p className="text-sm font-medium">{content.creator_name}</p>
              <p className="text-xs text-muted-foreground">{timeAgo(content.created_at)}</p>
            </div>
          </div>
        </div>
        <h3 className="font-semibold line-clamp-1">{content.title}</h3>
      </CardHeader>
      <CardContent className="pb-2">
        <p className="text-sm text-muted-foreground line-clamp-2">{content.description}</p>
        <div className="mt-2 flex flex-wrap gap-1">
          {content.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="text-xs text-primary">#{tag}</span>
          ))}
        </div>
      </CardContent>
      <CardFooter className="border-t pt-3">
        <div className="flex w-full items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1"><Eye className="h-4 w-4" />{formatNumber(content.views)}</span>
            <span className="flex items-center gap-1"><Heart className="h-4 w-4" />{formatNumber(content.likes)}</span>
            <span className="flex items-center gap-1"><MessageCircle className="h-4 w-4" />{formatNumber(content.comments)}</span>
          </div>
          <span className="font-medium text-foreground">{formatCurrency(content.earnings)}</span>
        </div>
      </CardFooter>
    </Card>
  );
}
