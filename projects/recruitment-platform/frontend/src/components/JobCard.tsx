"use client";

import React from "react";
import { Job } from "@/lib/types";
import { Card, CardContent, CardFooter } from "./Card";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
import { MapPin, Clock, Users, Eye, DollarSign } from "lucide-react";

interface JobCardProps {
  job: Job;
  onView?: (job: Job) => void;
  onEdit?: (job: Job) => void;
  onDelete?: (job: Job) => void;
  className?: string;
}

const statusColors: Record<Job["status"], { variant: "success" | "error" | "warning" | "default"; label: string }> = {
  open: { variant: "success", label: "Open" },
  closed: { variant: "error", label: "Closed" },
  draft: { variant: "default", label: "Draft" },
  "on-hold": { variant: "warning", label: "On Hold" },
};

const typeLabels: Record<Job["type"], string> = {
  "full-time": "Full-time",
  "part-time": "Part-time",
  contract: "Contract",
  remote: "Remote",
};

export function JobCard({ job, onView, onEdit, onDelete, className }: JobCardProps) {
  const status = statusColors[job.status];

  return (
    <Card variant="bordered" padding="md" className={cn("hover:shadow-md transition-shadow", className)}>
      <CardContent>
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{job.title}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">{job.department}</p>
          </div>
          <Badge variant={status.variant} size="sm">{status.label}</Badge>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-3">{job.description}</p>
        <div className="flex flex-wrap gap-3 text-sm text-gray-500 dark:text-gray-400">
          <span className="inline-flex items-center gap-1">
            <MapPin className="h-4 w-4" /> {job.location}
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock className="h-4 w-4" /> {typeLabels[job.type]}
          </span>
          <span className="inline-flex items-center gap-1">
            <DollarSign className="h-4 w-4" /> {formatCurrency(job.salary.min)} - {formatCurrency(job.salary.max)}
          </span>
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.requirements.slice(0, 3).map((req) => (
            <Badge key={req} variant="outline" size="sm">{req}</Badge>
          ))}
          {job.requirements.length > 3 && (
            <Badge variant="outline" size="sm">+{job.requirements.length - 3}</Badge>
          )}
        </div>
      </CardContent>
      <CardFooter>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
            <span className="inline-flex items-center gap-1">
              <Users className="h-4 w-4" /> {job.applicants} applicants
            </span>
            <span className="inline-flex items-center gap-1">
              <Eye className="h-4 w-4" /> {job.views} views
            </span>
          </div>
          <div className="flex gap-2">
            {onView && <Button variant="ghost" size="sm" onClick={() => onView(job)}>View</Button>}
            {onEdit && <Button variant="outline" size="sm" onClick={() => onEdit(job)}>Edit</Button>}
            {onDelete && <Button variant="destructive" size="sm" onClick={() => onDelete(job)}>Delete</Button>}
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}
