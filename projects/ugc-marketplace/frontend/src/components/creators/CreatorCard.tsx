"use client";

import { BadgeCheck, MoreVertical, Mail, UserPlus, UserMinus } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Avatar } from "../ui/Avatar";
import { Button } from "../ui/Button";
import { formatNumber, formatCurrency } from "@/lib/utils";
import type { Creator } from "@/lib/types";
import { useState } from "react";

interface CreatorCardProps {
  creator: Creator;
  onMessage?: (id: string) => void;
  onToggleFollow?: (id: string) => void;
  isFollowing?: boolean;
}

export function CreatorCard({ creator, onMessage, onToggleFollow, isFollowing }: CreatorCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  const statusColors = {
    active: "success",
    pending: "warning",
    suspended: "destructive",
  } as const;

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Avatar src={creator.avatar} alt={creator.name} size="lg" />
            <div>
              <div className="flex items-center gap-1.5">
                <h3 className="font-semibold">{creator.name}</h3>
                {creator.verified && <BadgeCheck className="h-4 w-4 text-primary" />}
              </div>
              <p className="text-sm text-muted-foreground">@{creator.username}</p>
            </div>
          </div>
          <div className="relative">
            <Button variant="ghost" size="icon" onClick={() => setShowMenu(!showMenu)}>
              <MoreVertical className="h-4 w-4" />
            </Button>
            {showMenu && (
              <div className="absolute right-0 top-full z-10 mt-1 w-40 rounded-md border bg-card p-1 shadow-lg">
                <button className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent" onClick={() => { onMessage?.(creator.id); setShowMenu(false); }}>
                  <Mail className="h-4 w-4" /> Message
                </button>
                <button className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent" onClick={() => { onToggleFollow?.(creator.id); setShowMenu(false); }}>
                  {isFollowing ? <><UserMinus className="h-4 w-4" /> Unfollow</> : <><UserPlus className="h-4 w-4" /> Follow</>}
                </button>
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <p className="text-sm text-muted-foreground line-clamp-2">{creator.bio}</p>
        <div className="mt-3 flex flex-wrap gap-1">
          {creator.categories.slice(0, 3).map((cat) => (
            <Badge key={cat} variant="secondary" className="text-xs">{cat}</Badge>
          ))}
        </div>
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-lg font-semibold">{formatNumber(creator.followers)}</p>
            <p className="text-xs text-muted-foreground">Followers</p>
          </div>
          <div>
            <p className="text-lg font-semibold">{creator.engagement_rate}%</p>
            <p className="text-xs text-muted-foreground">Engagement</p>
          </div>
          <div>
            <p className="text-lg font-semibold">{formatCurrency(creator.total_earnings)}</p>
            <p className="text-xs text-muted-foreground">Earned</p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="border-t pt-3">
        <div className="flex w-full items-center justify-between">
          <Badge variant={statusColors[creator.status]}>{creator.status}</Badge>
          <span className="text-xs text-muted-foreground">{creator.content_count} pieces</span>
        </div>
      </CardFooter>
    </Card>
  );
}
