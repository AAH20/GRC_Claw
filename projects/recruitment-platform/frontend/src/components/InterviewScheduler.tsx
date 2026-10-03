"use client";

import React, { useState } from "react";
import { Interview } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "./Card";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { Avatar } from "./Avatar";
import { Modal } from "./Modal";
import { Input } from "./Input";
import { cn, formatDate, formatDateTime, getInitials } from "@/lib/utils";
import { Calendar, Clock, MapPin, Video, Users, Plus, X } from "lucide-react";

interface InterviewSchedulerProps {
  interviews: Interview[];
  isLoading?: boolean;
  onSchedule?: (interview: Omit<Interview, "id">) => void;
  onCancel?: (id: string) => void;
  onReschedule?: (id: string, date: string, time: string) => void;
}

const statusColors: Record<Interview["status"], { variant: "success" | "error" | "warning" | "default"; label: string }> = {
  scheduled: { variant: "info", label: "Scheduled" },
  completed: { variant: "success", label: "Completed" },
  cancelled: { variant: "error", label: "Cancelled" },
  "no-show": { variant: "warning", label: "No Show" },
};

const typeIcons: Record<Interview["type"], React.ReactNode> = {
  phone: <Clock className="h-4 w-4" />,
  video: <Video className="h-4 w-4" />,
  onsite: <MapPin className="h-4 w-4" />,
  technical: <Users className="h-4 w-4" />,
  behavioral: <Users className="h-4 w-4" />,
};

export function InterviewScheduler({
  interviews,
  isLoading = false,
  onSchedule,
  onCancel,
  onReschedule,
}: InterviewSchedulerProps) {
  const [showModal, setShowModal] = useState(false);
  const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null);
  const [formData, setFormData] = useState({
    candidateName: "",
    jobTitle: "",
    type: "video" as Interview["type"],
    date: "",
    time: "",
    duration: 60,
    interviewers: "",
    location: "",
    meetingUrl: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!onSchedule) return;
    onSchedule({
      candidateId: "temp",
      candidateName: formData.candidateName,
      jobId: "temp",
      jobTitle: formData.jobTitle,
      type: formData.type,
      date: formData.date,
      time: formData.time,
      duration: formData.duration,
      interviewers: formData.interviewers.split(",").map((s) => s.trim()).filter(Boolean),
      status: "scheduled",
      location: formData.location,
      meetingUrl: formData.meetingUrl,
    });
    setShowModal(false);
    setFormData({ candidateName: "", jobTitle: "", type: "video", date: "", time: "", duration: 60, interviewers: "", location: "", meetingUrl: "" });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Interviews</h2>
        {onSchedule && (
          <Button onClick={() => setShowModal(true)} leftIcon={<Plus className="h-4 w-4" />}>
            Schedule Interview
          </Button>
        )}
      </div>

      {interviews.length === 0 ? (
        <Card>
          <div className="py-12 text-center">
            <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">No interviews scheduled</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {interviews.map((interview) => {
            const status = statusColors[interview.status];
            return (
              <Card key={interview.id} variant="bordered" padding="md">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <Avatar alt={interview.candidateName} fallback={getInitials(interview.candidateName)} size="md" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">{interview.candidateName}</h3>
                      <Badge variant={status.variant} size="sm">{status.label}</Badge>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{interview.jobTitle}</p>
                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                      <span className="inline-flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" /> {formatDate(interview.date)}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" /> {interview.time} ({interview.duration}min)
                      </span>
                      <span className="inline-flex items-center gap-1">
                        {typeIcons[interview.type]} {interview.type}
                      </span>
                      {interview.location && (
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" /> {interview.location}
                        </span>
                      )}
                    </div>
                    {interview.interviewers.length > 0 && (
                      <div className="mt-2 flex items-center gap-1">
                        <Users className="h-3.5 w-3.5 text-gray-400" />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {interview.interviewers.join(", ")}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {onReschedule && interview.status === "scheduled" && (
                      <Button variant="outline" size="sm" onClick={() => setSelectedInterview(interview)}>
                        Reschedule
                      </Button>
                    )}
                    {onCancel && interview.status === "scheduled" && (
                      <Button variant="destructive" size="sm" onClick={() => onCancel(interview.id)}>
                        <X className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Schedule Interview" size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Candidate Name" value={formData.candidateName} onChange={(e) => setFormData({ ...formData, candidateName: e.target.value })} required />
            <Input label="Job Title" value={formData.jobTitle} onChange={(e) => setFormData({ ...formData, jobTitle: e.target.value })} required />
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Type</label>
              <select value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value as Interview["type"] })} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm">
                <option value="phone">Phone</option>
                <option value="video">Video</option>
                <option value="onsite">On-site</option>
                <option value="technical">Technical</option>
                <option value="behavioral">Behavioral</option>
              </select>
            </div>
            <Input label="Duration (min)" type="number" value={formData.duration} onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) })} required />
            <Input label="Date" type="date" value={formData.date} onChange={(e) => setFormData({ ...formData, date: e.target.value })} required />
            <Input label="Time" type="time" value={formData.time} onChange={(e) => setFormData({ ...formData, time: e.target.value })} required />
            <Input label="Interviewers (comma-separated)" value={formData.interviewers} onChange={(e) => setFormData({ ...formData, interviewers: e.target.value })} />
            <Input label="Location / Meeting URL" value={formData.location || formData.meetingUrl} onChange={(e) => setFormData({ ...formData, location: e.target.value })} />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button type="submit">Schedule</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={!!selectedInterview} onClose={() => setSelectedInterview(null)} title="Reschedule Interview" size="md">
        {selectedInterview && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Reschedule interview for <strong>{selectedInterview.candidateName}</strong>
            </p>
            <Input label="New Date" type="date" value={selectedInterview.date} onChange={(e) => setSelectedInterview({ ...selectedInterview, date: e.target.value })} />
            <Input label="New Time" type="time" value={selectedInterview.time} onChange={(e) => setSelectedInterview({ ...selectedInterview, time: e.target.value })} />
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setSelectedInterview(null)}>Cancel</Button>
              <Button onClick={() => {
                if (onReschedule) onReschedule(selectedInterview.id, selectedInterview.date, selectedInterview.time);
                setSelectedInterview(null);
              }}>Confirm</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
