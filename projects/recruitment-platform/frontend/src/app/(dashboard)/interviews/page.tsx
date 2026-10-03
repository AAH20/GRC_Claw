"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Avatar } from "@/components/Avatar";
import { Modal } from "@/components/Modal";
import { Input } from "@/components/Input";
import { cn, formatDate, getInitials } from "@/lib/utils";
import { Calendar, Clock, MapPin, Video, Users, Plus, X, Edit, Trash2 } from "lucide-react";

const mockInterviews = [
  { id: "1", candidateId: "1", candidateName: "Sarah Johnson", jobId: "1", jobTitle: "Senior Frontend Developer", type: "video", date: "2024-01-16", time: "10:00", duration: 60, interviewers: ["John Doe", "Jane Smith"], status: "scheduled", location: "", meetingUrl: "https://meet.example.com/abc" },
  { id: "2", candidateId: "2", candidateName: "Michael Chen", jobId: "2", jobTitle: "Backend Developer", type: "onsite", date: "2024-01-16", time: "14:00", duration: 90, interviewers: ["Alice Brown"], status: "scheduled", location: "Conference Room A" },
  { id: "3", candidateId: "3", candidateName: "Emily Davis", jobId: "3", jobTitle: "Product Manager", type: "phone", date: "2024-01-17", time: "11:00", duration: 45, interviewers: ["Bob Wilson", "Carol White"], status: "scheduled" },
  { id: "4", candidateId: "4", candidateName: "James Wilson", jobId: "4", jobTitle: "DevOps Engineer", type: "technical", date: "2024-01-15", time: "09:00", duration: 120, interviewers: ["David Lee", "Eva Green"], status: "completed", rating: 5, feedback: "Excellent technical skills" },
  { id: "5", candidateId: "5", candidateName: "Lisa Anderson", jobId: "5", jobTitle: "UX Designer", type: "behavioral", date: "2024-01-14", time: "15:00", duration: 60, interviewers: ["Frank Black"], status: "completed", rating: 4, feedback: "Good cultural fit" },
  { id: "6", candidateId: "6", candidateName: "David Brown", jobId: "6", jobTitle: "Data Scientist", type: "video", date: "2024-01-13", time: "10:00", duration: 60, interviewers: ["Grace Kim"], status: "cancelled" },
];

const statusColors: Record<string, { variant: "success" | "error" | "warning" | "default"; label: string }> = {
  scheduled: { variant: "info", label: "Scheduled" },
  completed: { variant: "success", label: "Completed" },
  cancelled: { variant: "error", label: "Cancelled" },
  "no-show": { variant: "warning", label: "No Show" },
};

const typeIcons: Record<string, React.ReactNode> = {
  phone: <Clock className="h-4 w-4" />,
  video: <Video className="h-4 w-4" />,
  onsite: <MapPin className="h-4 w-4" />,
  technical: <Users className="h-4 w-4" />,
  behavioral: <Users className="h-4 w-4" />,
};

export default function InterviewsPage() {
  const [showModal, setShowModal] = useState(false);
  const [selectedInterview, setSelectedInterview] = useState<typeof mockInterviews[0] | null>(null);
  const [formData, setFormData] = useState({
    candidateName: "",
    jobTitle: "",
    type: "video" as string,
    date: "",
    time: "",
    duration: 60,
    interviewers: "",
    location: "",
    meetingUrl: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowModal(false);
    setFormData({ candidateName: "", jobTitle: "", type: "video", date: "", time: "", duration: 60, interviewers: "", location: "", meetingUrl: "" });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Interviews</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Schedule and manage interviews</p>
        </div>
        <Button onClick={() => setShowModal(true)} leftIcon={<Plus className="h-4 w-4" />}>
          Schedule Interview
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card variant="bordered" padding="md">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
              <Calendar className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Scheduled</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{mockInterviews.filter((i) => i.status === "scheduled").length}</p>
            </div>
          </div>
        </Card>
        <Card variant="bordered" padding="md">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
              <Users className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Completed</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{mockInterviews.filter((i) => i.status === "completed").length}</p>
            </div>
          </div>
        </Card>
        <Card variant="bordered" padding="md">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400">
              <X className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Cancelled</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{mockInterviews.filter((i) => i.status === "cancelled").length}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Interviews List */}
      <div className="space-y-3">
        {mockInterviews.map((interview) => {
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
                    <span className="inline-flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{formatDate(interview.date)}</span>
                    <span className="inline-flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{interview.time} ({interview.duration}min)</span>
                    <span className="inline-flex items-center gap-1">{typeIcons[interview.type]}{interview.type}</span>
                    {interview.location && <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{interview.location}</span>}
                  </div>
                  {interview.interviewers.length > 0 && (
                    <div className="mt-2 flex items-center gap-1">
                      <Users className="h-3.5 w-3.5 text-gray-400" />
                      <span className="text-xs text-gray-500 dark:text-gray-400">{interview.interviewers.join(", ")}</span>
                    </div>
                  )}
                  {interview.feedback && (
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 italic">&quot;{interview.feedback}&quot;</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {interview.status === "scheduled" && (
                    <>
                      <Button variant="outline" size="sm" onClick={() => setSelectedInterview(interview)}>Reschedule</Button>
                      <Button variant="destructive" size="sm" onClick={() => {}}><X className="h-3.5 w-3.5" /></Button>
                    </>
                  )}
                  {interview.status === "completed" && interview.rating && (
                    <div className="flex items-center gap-0.5">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <span key={i} className={cn("text-sm", i < (interview.rating || 0) ? "text-yellow-400" : "text-gray-300 dark:text-gray-600")}>★</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Schedule Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Schedule Interview" size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Candidate Name" value={formData.candidateName} onChange={(e) => setFormData({ ...formData, candidateName: e.target.value })} required />
            <Input label="Job Title" value={formData.jobTitle} onChange={(e) => setFormData({ ...formData, jobTitle: e.target.value })} required />
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Type</label>
              <select value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value })} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm">
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
            <Input label="Location / Meeting URL" value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button type="submit">Schedule</Button>
          </div>
        </form>
      </Modal>

      {/* Reschedule Modal */}
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
              <Button onClick={() => setSelectedInterview(null)}>Confirm</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
