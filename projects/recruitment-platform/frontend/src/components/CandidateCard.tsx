"use client";

import React from "react";
import { Candidate } from "@/lib/types";
import { Card, CardContent, CardFooter } from "./Card";
import { Badge } from "./Badge";
import { Avatar } from "./Avatar";
import { Button } from "./Button";
import { cn, formatDate, getInitials } from "@/lib/utils";
import { Star, MapPin, Briefcase, Mail, Phone } from "lucide-react";

interface CandidateCardProps {
  candidate: Candidate;
  onView?: (candidate: Candidate) => void;
  onEdit?: (candidate: Candidate) => void;
  onDelete?: (candidate: Candidate) => void;
  className?: string;
}

const statusColors: Record<Candidate["status"], { variant: "success" | "info" | "warning" | "error" | "default"; label: string }> = {
  new: { variant: "info", label: "New" },
  screening: { variant: "warning", label: "Screening" },
  interview: { variant: "default", label: "Interview" },
  offer: { variant: "success", label: "Offer" },
  hired: { variant: "success", label: "Hired" },
  rejected: { variant: "error", label: "Rejected" },
};

export function CandidateCard({ candidate, onView, onEdit, onDelete, className }: CandidateCardProps) {
  const status = statusColors[candidate.status];

  return (
    <Card variant="bordered" padding="md" className={cn("hover:shadow-md transition-shadow", className)}>
      <CardContent>
        <div className="flex items-start gap-4">
          <Avatar src={candidate.avatar} alt={candidate.name} fallback={getInitials(candidate.name)} size="lg" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{candidate.name}</h3>
              <Badge variant={status.variant} size="sm">{status.label}</Badge>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 mb-1">
              <Mail className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="truncate">{candidate.email}</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 mb-2">
              <Phone className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{candidate.phone}</span>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-3 w-3" aria-hidden="true" /> {candidate.location}
              </span>
              <span className="inline-flex items-center gap-1">
                <Briefcase className="h-3 w-3" aria-hidden="true" /> {candidate.experience}y exp
              </span>
            </div>
          </div>
          <div className="flex items-center gap-0.5" aria-label={`Rating: ${candidate.rating} out of 5 stars`}>
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className={cn(
                  "h-4 w-4",
                  i < candidate.rating ? "text-yellow-400 fill-yellow-400" : "text-gray-300 dark:text-gray-600"
                )}
                aria-hidden="true"
              />
            ))}
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {candidate.skills.slice(0, 4).map((skill) => (
            <Badge key={skill} variant="outline" size="sm">{skill}</Badge>
          ))}
          {candidate.skills.length > 4 && (
            <Badge variant="outline" size="sm">+{candidate.skills.length - 4}</Badge>
          )}
        </div>
      </CardContent>
      <CardFooter>
        <div className="flex items-center justify-between w-full">
          <span className="text-xs text-gray-400 dark:text-gray-500">
            Applied {formatDate(candidate.appliedDate)}
          </span>
          <div className="flex gap-2">
            {onView && (
              <Button variant="ghost" size="sm" onClick={() => onView(candidate)} aria-label={`View candidate: ${candidate.name}`}>View</Button>
            )}
            {onEdit && (
              <Button variant="outline" size="sm" onClick={() => onEdit(candidate)} aria-label={`Edit candidate: ${candidate.name}`}>Edit</Button>
            )}
            {onDelete && (
              <Button variant="destructive" size="sm" onClick={() => onDelete(candidate)} aria-label={`Delete candidate: ${candidate.name}`}>Delete</Button>
            )}
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}
