export interface Candidate {
  id: string;
  name: string;
  email: string;
  phone: string;
  avatar?: string;
  status: "new" | "screening" | "interview" | "offer" | "hired" | "rejected";
  skills: string[];
  experience: number;
  location: string;
  appliedDate: string;
  jobId: string;
  rating: number;
  notes?: string;
}

export interface Job {
  id: string;
  title: string;
  department: string;
  location: string;
  type: "full-time" | "part-time" | "contract" | "remote";
  salary: { min: number; max: number; currency: string };
  description: string;
  requirements: string[];
  status: "open" | "closed" | "draft" | "on-hold";
  postedDate: string;
  closingDate?: string;
  applicants: number;
  views: number;
}

export interface Application {
  id: string;
  candidateId: string;
  candidateName: string;
  candidateEmail: string;
  jobId: string;
  jobTitle: string;
  status: "pending" | "reviewing" | "shortlisted" | "rejected" | "hired";
  appliedDate: string;
  updatedDate: string;
  resumeUrl?: string;
  coverLetter?: string;
  source: string;
  rating: number;
}

export interface Interview {
  id: string;
  candidateId: string;
  candidateName: string;
  jobId: string;
  jobTitle: string;
  type: "phone" | "video" | "onsite" | "technical" | "behavioral";
  date: string;
  time: string;
  duration: number;
  interviewers: string[];
  status: "scheduled" | "completed" | "cancelled" | "no-show";
  feedback?: string;
  rating?: number;
  location?: string;
  meetingUrl?: string;
}

export interface AnalyticsData {
  totalCandidates: number;
  totalJobs: number;
  totalApplications: number;
  totalInterviews: number;
  hireRate: number;
  avgTimeToHire: number;
  applicationsByMonth: { month: string; count: number }[];
  candidatesByStatus: { status: string; count: number }[];
  jobsByDepartment: { department: string; count: number }[];
  sourceBreakdown: { source: string; count: number }[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "recruiter" | "hiring-manager";
  avatar?: string;
  department?: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  read: boolean;
  createdAt: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
}
