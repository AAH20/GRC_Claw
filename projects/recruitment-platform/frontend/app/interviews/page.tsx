'use client';

import React, { useState, useMemo, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Candidate {
  id: string;
  name: string;
  email: string;
  phone: string;
  avatarUrl?: string;
}

interface Interview {
  id: string;
  candidate: Candidate;
  position: string;
  round: number;
  totalRounds: number;
  date: string; // ISO date string YYYY-MM-DD
  startTime: string; // HH:mm
  endTime: string; // HH:mm
  timezone: string;
  type: 'phone' | 'video' | 'onsite' | 'technical' | 'behavioral';
  status: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled' | 'no-show';
  interviewer: string;
  interviewerRole: string;
  location?: string;
  meetingLink?: string;
  notes?: string;
  feedback?: InterviewFeedback;
}

interface InterviewFeedback {
  rating: number; // 1-5
  technicalScore?: number; // 1-5
  communicationScore?: number; // 1-5
  cultureFitScore?: number; // 1-5
  strengths: string;
  weaknesses: string;
  recommendation: 'strong-hire' | 'hire' | 'lean-hire' | 'lean-no-hire' | 'no-hire';
  notes: string;
  submittedAt: string;
  submittedBy: string;
}

interface CalendarDay {
  date: Date;
  isCurrentMonth: boolean;
  isToday: boolean;
  interviews: Interview[];
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_INTERVIEWS: Interview[] = [
  {
    id: 'int-001',
    candidate: { id: 'cand-001', name: 'Sarah Chen', email: 'sarah.chen@email.com', phone: '+1-555-0101' },
    position: 'Senior Frontend Engineer',
    round: 2,
    totalRounds: 4,
    date: '2026-10-05',
    startTime: '10:00',
    endTime: '11:00',
    timezone: 'PST',
    type: 'video',
    status: 'scheduled',
    interviewer: 'James Wilson',
    interviewerRole: 'Engineering Manager',
    meetingLink: 'https://meet.example.com/sarah-chen',
  },
  {
    id: 'int-002',
    candidate: { id: 'cand-002', name: 'Marcus Johnson', email: 'marcus.j@email.com', phone: '+1-555-0102' },
    position: 'Backend Engineer',
    round: 1,
    totalRounds: 3,
    date: '2026-10-05',
    startTime: '14:00',
    endTime: '15:00',
    timezone: 'EST',
    type: 'technical',
    status: 'scheduled',
    interviewer: 'Priya Patel',
    interviewerRole: 'Tech Lead',
    meetingLink: 'https://meet.example.com/marcus-johnson',
  },
  {
    id: 'int-003',
    candidate: { id: 'cand-003', name: 'Emily Rodriguez', email: 'emily.r@email.com', phone: '+1-555-0103' },
    position: 'Product Designer',
    round: 3,
    totalRounds: 3,
    date: '2026-10-06',
    startTime: '09:00',
    endTime: '10:30',
    timezone: 'CST',
    type: 'onsite',
    status: 'scheduled',
    interviewer: 'Alex Kim',
    interviewerRole: 'Design Director',
    location: 'HQ – Building A, Conference Room 3',
  },
  {
    id: 'int-004',
    candidate: { id: 'cand-004', name: 'David Park', email: 'david.park@email.com', phone: '+1-555-0104' },
    position: 'DevOps Engineer',
    round: 2,
    totalRounds: 3,
    date: '2026-10-07',
    startTime: '11:00',
    endTime: '12:00',
    timezone: 'PST',
    type: 'video',
    status: 'scheduled',
    interviewer: 'Lisa Thompson',
    interviewerRole: 'DevOps Lead',
    meetingLink: 'https://meet.example.com/david-park',
  },
  {
    id: 'int-005',
    candidate: { id: 'cand-005', name: 'Aisha Patel', email: 'aisha.p@email.com', phone: '+1-555-0105' },
    position: 'Full Stack Developer',
    round: 1,
    totalRounds: 4,
    date: '2026-10-08',
    startTime: '15:00',
    endTime: '16:00',
    timezone: 'EST',
    type: 'phone',
    status: 'scheduled',
    interviewer: 'Tom Bradley',
    interviewerRole: 'Senior Recruiter',
  },
  {
    id: 'int-006',
    candidate: { id: 'cand-006', name: 'Ryan O\'Brien', email: 'ryan.ob@email.com', phone: '+1-555-0106' },
    position: 'Senior Frontend Engineer',
    round: 3,
    totalRounds: 4,
    date: '2026-10-03',
    startTime: '10:00',
    endTime: '11:30',
    timezone: 'PST',
    type: 'behavioral',
    status: 'completed',
    interviewer: 'James Wilson',
    interviewerRole: 'Engineering Manager',
    feedback: {
      rating: 4,
      technicalScore: 4,
      communicationScore: 5,
      cultureFitScore: 4,
      strengths: 'Strong React/TypeScript expertise, excellent communication, great system design sense.',
      weaknesses: 'Limited experience with micro-frontends, could improve on testing strategies.',
      recommendation: 'hire',
      notes: 'Impressive candidate. Recommend moving to final round.',
      submittedAt: '2026-10-03T12:00:00Z',
      submittedBy: 'James Wilson',
    },
  },
  {
    id: 'int-007',
    candidate: { id: 'cand-007', name: 'Nina Kowalski', email: 'nina.k@email.com', phone: '+1-555-0107' },
    position: 'Backend Engineer',
    round: 2,
    totalRounds: 3,
    date: '2026-10-02',
    startTime: '13:00',
    endTime: '14:00',
    timezone: 'CST',
    type: 'technical',
    status: 'completed',
    interviewer: 'Priya Patel',
    interviewerRole: 'Tech Lead',
    feedback: {
      rating: 3,
      technicalScore: 3,
      communicationScore: 4,
      cultureFitScore: 3,
      strengths: 'Solid Node.js skills, good problem-solving approach.',
      weaknesses: 'Struggled with distributed systems questions, limited cloud experience.',
      recommendation: 'lean-hire',
      notes: 'Borderline candidate. Consider additional technical screen.',
      submittedAt: '2026-10-02T15:00:00Z',
      submittedBy: 'Priya Patel',
    },
  },
  {
    id: 'int-008',
    candidate: { id: 'cand-008', name: 'Carlos Mendez', email: 'carlos.m@email.com', phone: '+1-555-0108' },
    position: 'Product Designer',
    round: 1,
    totalRounds: 3,
    date: '2026-10-09',
    startTime: '10:00',
    endTime: '11:00',
    timezone: 'EST',
    type: 'video',
    status: 'scheduled',
    interviewer: 'Alex Kim',
    interviewerRole: 'Design Director',
    meetingLink: 'https://meet.example.com/carlos-mendez',
  },
  {
    id: 'int-009',
    candidate: { id: 'cand-009', name: 'Jessica Liu', email: 'jessica.liu@email.com', phone: '+1-555-0109' },
    position: 'DevOps Engineer',
    round: 1,
    totalRounds: 3,
    date: '2026-10-10',
    startTime: '09:30',
    endTime: '10:30',
    timezone: 'PST',
    type: 'phone',
    status: 'scheduled',
    interviewer: 'Lisa Thompson',
    interviewerRole: 'DevOps Lead',
  },
  {
    id: 'int-010',
    candidate: { id: 'cand-010', name: 'Omar Hassan', email: 'omar.h@email.com', phone: '+1-555-0110' },
    position: 'Full Stack Developer',
    round: 2,
    totalRounds: 4,
    date: '2026-10-12',
    startTime: '14:00',
    endTime: '15:30',
    timezone: 'EST',
    type: 'onsite',
    status: 'scheduled',
    interviewer: 'Tom Bradley',
    interviewerRole: 'Senior Recruiter',
    location: 'HQ – Building B, Conference Room 1',
  },
];

// ─── Utility Helpers ─────────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTime(time: string): string {
  const [hours, minutes] = time.split(':').map(Number);
  const period = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;
  return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
}

function getStatusColor(status: Interview['status']): string {
  const colors: Record<Interview['status'], string> = {
    scheduled: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
    rescheduled: 'bg-yellow-100 text-yellow-800',
    'no-show': 'bg-gray-100 text-gray-800',
  };
  return colors[status];
}

function getTypeIcon(type: Interview['type']): string {
  const icons: Record<Interview['type'], string> = {
    phone: '📞',
    video: '💻',
    onsite: '🏢',
    technical: '⚙️',
    behavioral: '🤝',
  };
  return icons[type];
}

function getRecommendationColor(rec: InterviewFeedback['recommendation']): string {
  const colors: Record<InterviewFeedback['recommendation'], string> = {
    'strong-hire': 'bg-green-100 text-green-800',
    hire: 'bg-emerald-100 text-emerald-800',
    'lean-hire': 'bg-yellow-100 text-yellow-800',
    'lean-no-hire': 'bg-orange-100 text-orange-800',
    'no-hire': 'bg-red-100 text-red-800',
  };
  return colors[rec];
}

// ─── Sub-Components ──────────────────────────────────────────────────────────

interface InterviewCalendarProps {
  interviews: Interview[];
  selectedDate: Date | null;
  onSelectDate: (date: Date) => void;
}

const InterviewCalendar: React.FC<InterviewCalendarProps> = ({ interviews, selectedDate, onSelectDate }) => {
  const [currentMonth, setCurrentMonth] = useState(new Date(2026, 9, 1)); // October 2026

  const calendarDays = useMemo((): CalendarDay[] => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPad = firstDay.getDay();

    const days: CalendarDay[] = [];

    // Previous month padding
    for (let i = startPad - 1; i >= 0; i--) {
      const date = new Date(year, month, -i);
      days.push({
        date,
        isCurrentMonth: false,
        isToday: false,
        interviews: getInterviewsForDate(interviews, date),
      });
    }

    // Current month
    for (let d = 1; d <= lastDay.getDate(); d++) {
      const date = new Date(year, month, d);
      const today = new Date();
      days.push({
        date,
        isCurrentMonth: true,
        isToday: date.toDateString() === today.toDateString(),
        interviews: getInterviewsForDate(interviews, date),
      });
    }

    // Next month padding
    const remaining = 42 - days.length;
    for (let i = 1; i <= remaining; i++) {
      const date = new Date(year, month + 1, i);
      days.push({
        date,
        isCurrentMonth: false,
        isToday: false,
        interviews: getInterviewsForDate(interviews, date),
      });
    }

    return days;
  }, [currentMonth, interviews]);

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const goToPrevMonth = () => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  const goToNextMonth = () => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          {currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
        </h2>
        <div className="flex gap-2">
          <button
            onClick={goToPrevMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Previous month"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            onClick={goToNextMonth}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Next month"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-1 mb-2">
        {weekDays.map((day) => (
          <div key={day} className="text-center text-xs font-medium text-gray-500 py-2">
            {day}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {calendarDays.map((day, idx) => {
          const isSelected = selectedDate && day.date.toDateString() === selectedDate.toDateString();
          const hasInterviews = day.interviews.length > 0;

          return (
            <button
              key={idx}
              onClick={() => onSelectDate(day.date)}
              className={`
                relative p-2 min-h-[60px] sm:min-h-[80px] rounded-lg text-sm transition-all text-left
                ${day.isCurrentMonth ? 'text-gray-900' : 'text-gray-400'}
                ${isSelected ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}
                ${day.isToday && !isSelected ? 'ring-2 ring-blue-500' : ''}
              `}
            >
              <span className={`font-medium ${isSelected ? 'text-white' : ''}`}>
                {day.date.getDate()}
              </span>
              {hasInterviews && (
                <div className="mt-1 space-y-0.5">
                  {day.interviews.slice(0, 2).map((interview) => (
                    <div
                      key={interview.id}
                      className={`text-[10px] sm:text-xs truncate px-1 py-0.5 rounded ${
                        isSelected ? 'bg-blue-500 text-white' : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {interview.startTime} {interview.candidate.name.split(' ')[0]}
                    </div>
                  ))}
                  {day.interviews.length > 2 && (
                    <div className={`text-[10px] ${isSelected ? 'text-blue-100' : 'text-gray-500'}`}>
                      +{day.interviews.length - 2} more
                    </div>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

function getInterviewsForDate(interviews: Interview[], date: Date): Interview[] {
  const dateStr = date.toISOString().split('T')[0];
  return interviews.filter((i) => i.date === dateStr);
}

// ─── Upcoming Interviews List ────────────────────────────────────────────────

interface UpcomingInterviewsListProps {
  interviews: Interview[];
  onViewFeedback: (interview: Interview) => void;
  onReschedule: (interview: Interview) => void;
}

const UpcomingInterviewsList: React.FC<UpcomingInterviewsListProps> = ({ interviews, onViewFeedback, onReschedule }) => {
  const upcoming = useMemo(
    () =>
      interviews
        .filter((i) => i.status === 'scheduled')
        .sort((a, b) => new Date(a.date + 'T' + a.startTime).getTime() - new Date(b.date + 'T' + b.startTime).getTime()),
    [interviews]
  );

  if (upcoming.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
        <p className="text-gray-500">No upcoming interviews scheduled.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4 sm:p-6 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Upcoming Interviews</h2>
        <p className="text-sm text-gray-500 mt-1">{upcoming.length} interview{upcoming.length !== 1 ? 's' : ''} scheduled</p>
      </div>
      <div className="divide-y divide-gray-100">
        {upcoming.map((interview) => (
          <div key={interview.id} className="p-4 sm:p-6 hover:bg-gray-50 transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-lg">
                  {getTypeIcon(interview.type)}
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">{interview.candidate.name}</h3>
                  <p className="text-sm text-gray-600">{interview.position}</p>
                  <div className="flex flex-wrap items-center gap-2 mt-1">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(interview.status)}`}>
                      {interview.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      Round {interview.round}/{interview.totalRounds}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex flex-col sm:items-end gap-2">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">{formatDate(interview.date)}</span>
                  <span className="mx-1">·</span>
                  <span>{formatTime(interview.startTime)} – {formatTime(interview.endTime)}</span>
                </div>
                <div className="text-xs text-gray-500">
                  with {interview.interviewer} ({interview.interviewerRole})
                </div>
                <div className="flex gap-2 mt-1">
                  <button
                    onClick={() => onViewFeedback(interview)}
                    className="px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                  >
                    Feedback
                  </button>
                  <button
                    onClick={() => onReschedule(interview)}
                    className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    Reschedule
                  </button>
                </div>
              </div>
            </div>
            {interview.meetingLink && (
              <div className="mt-2 ml-13">
                <a
                  href={interview.meetingLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  Join Meeting →
                </a>
              </div>
            )}
            {interview.location && (
              <div className="mt-2 ml-13 text-xs text-gray-500">
                📍 {interview.location}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Interview Feedback Form ──────────────────────────────────────────────────

interface InterviewFeedbackFormProps {
  interview: Interview;
  onSubmit: (feedback: InterviewFeedback) => void;
  onCancel: () => void;
}

const InterviewFeedbackForm: React.FC<InterviewFeedbackFormProps> = ({ interview, onSubmit, onCancel }) => {
  const [rating, setRating] = useState(interview.feedback?.rating ?? 0);
  const [technicalScore, setTechnicalScore] = useState(interview.feedback?.technicalScore ?? 0);
  const [communicationScore, setCommunicationScore] = useState(interview.feedback?.communicationScore ?? 0);
  const [cultureFitScore, setCultureFitScore] = useState(interview.feedback?.cultureFitScore ?? 0);
  const [strengths, setStrengths] = useState(interview.feedback?.strengths ?? '');
  const [weaknesses, setWeaknesses] = useState(interview.feedback?.weaknesses ?? '');
  const [recommendation, setRecommendation] = useState<InterviewFeedback['recommendation']>(
    interview.feedback?.recommendation ?? 'lean-hire'
  );
  const [notes, setNotes] = useState(interview.feedback?.notes ?? '');
  const [hoveredStar, setHoveredStar] = useState(0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) return;

    const feedback: InterviewFeedback = {
      rating,
      technicalScore: technicalScore || undefined,
      communicationScore: communicationScore || undefined,
      cultureFitScore: cultureFitScore || undefined,
      strengths,
      weaknesses,
      recommendation,
      notes,
      submittedAt: new Date().toISOString(),
      submittedBy: 'Current User',
    };
    onSubmit(feedback);
  };

  const recommendations: { value: InterviewFeedback['recommendation']; label: string }[] = [
    { value: 'strong-hire', label: 'Strong Hire' },
    { value: 'hire', label: 'Hire' },
    { value: 'lean-hire', label: 'Lean Hire' },
    { value: 'lean-no-hire', label: 'Lean No Hire' },
    { value: 'no-hire', label: 'No Hire' },
  ];

  const StarRating: React.FC<{
    value: number;
    onChange: (v: number) => void;
    hovered: number;
    onHover: (v: number) => void;
    label: string;
  }> = ({ value, onChange, hovered, onHover, label }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => onChange(star)}
            onMouseEnter={() => onHover(star)}
            onMouseLeave={() => onHover(0)}
            className="p-0.5"
            aria-label={`${star} star${star > 1 ? 's' : ''}`}
          >
            <svg
              className={`w-6 h-6 transition-colors ${
                star <= (hovered || value) ? 'text-yellow-400' : 'text-gray-300'
              }`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4 sm:p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Interview Feedback</h2>
            <p className="text-sm text-gray-500 mt-1">
              {interview.candidate.name} — {interview.position} (Round {interview.round}/{interview.totalRounds})
            </p>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-6">
        {/* Overall Rating */}
        <StarRating
          value={rating}
          onChange={setRating}
          hovered={hoveredStar}
          onHover={setHoveredStar}
          label="Overall Rating *"
        />

        {/* Sub-scores */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StarRating
            value={technicalScore}
            onChange={setTechnicalScore}
            hovered={0}
            onHover={() => {}}
            label="Technical"
          />
          <StarRating
            value={communicationScore}
            onChange={setCommunicationScore}
            hovered={0}
            onHover={() => {}}
            label="Communication"
          />
          <StarRating
            value={cultureFitScore}
            onChange={setCultureFitScore}
            hovered={0}
            onHover={() => {}}
            label="Culture Fit"
          />
        </div>

        {/* Recommendation */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Recommendation *</label>
          <div className="flex flex-wrap gap-2">
            {recommendations.map((rec) => (
              <button
                key={rec.value}
                type="button"
                onClick={() => setRecommendation(rec.value)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  recommendation === rec.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {rec.label}
              </button>
            ))}
          </div>
        </div>

        {/* Strengths */}
        <div>
          <label htmlFor="strengths" className="block text-sm font-medium text-gray-700 mb-1">
            Strengths
          </label>
          <textarea
            id="strengths"
            value={strengths}
            onChange={(e) => setStrengths(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            placeholder="What did the candidate do well?"
          />
        </div>

        {/* Weaknesses */}
        <div>
          <label htmlFor="weaknesses" className="block text-sm font-medium text-gray-700 mb-1">
            Areas for Improvement
          </label>
          <textarea
            id="weaknesses"
            value={weaknesses}
            onChange={(e) => setWeaknesses(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            placeholder="What could the candidate improve?"
          />
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
            Additional Notes
          </label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            placeholder="Any other observations..."
          />
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={rating === 0}
            className="flex-1 px-4 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Submit Feedback
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

// ─── Reschedule Interview Modal ──────────────────────────────────────────────

interface RescheduleInterviewModalProps {
  interview: Interview;
  onConfirm: (newDate: string, newStartTime: string, newEndTime: string) => void;
  onClose: () => void;
}

const RescheduleInterviewModal: React.FC<RescheduleInterviewModalProps> = ({ interview, onConfirm, onClose }) => {
  const [newDate, setNewDate] = useState(interview.date);
  const [newStartTime, setNewStartTime] = useState(interview.startTime);
  const [newEndTime, setNewEndTime] = useState(interview.endTime);
  const [reason, setReason] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConfirm(newDate, newStartTime, newEndTime);
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Reschedule Interview</h2>
              <p className="text-sm text-gray-500 mt-1">
                {interview.candidate.name} — {interview.position}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Close modal"
            >
              <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4">
          {/* Current schedule */}
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Current Schedule</p>
            <p className="text-sm text-gray-900">
              {formatDate(interview.date)} · {formatTime(interview.startTime)} – {formatTime(interview.endTime)} {interview.timezone}
            </p>
          </div>

          {/* New date */}
          <div>
            <label htmlFor="new-date" className="block text-sm font-medium text-gray-700 mb-1">
              New Date *
            </label>
            <input
              id="new-date"
              type="date"
              value={newDate}
              min={today}
              onChange={(e) => setNewDate(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* New time */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="new-start" className="block text-sm font-medium text-gray-700 mb-1">
                Start Time *
              </label>
              <input
                id="new-start"
                type="time"
                value={newStartTime}
                onChange={(e) => setNewStartTime(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="new-end" className="block text-sm font-medium text-gray-700 mb-1">
                End Time *
              </label>
              <input
                id="new-end"
                type="time"
                value={newEndTime}
                onChange={(e) => setNewEndTime(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Reason */}
          <div>
            <label htmlFor="reschedule-reason" className="block text-sm font-medium text-gray-700 mb-1">
              Reason for Rescheduling
            </label>
            <textarea
              id="reschedule-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              placeholder="Optional: explain why this interview is being rescheduled"
            />
          </div>

          {/* Notification notice */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-xs text-blue-800">
              📧 The candidate and interviewer will be notified of the new schedule via email.
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <button
              type="submit"
              className="flex-1 px-4 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Confirm Reschedule
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function InterviewsPage() {
  const [interviews, setInterviews] = useState<Interview[]>(MOCK_INTERVIEWS);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [feedbackInterview, setFeedbackInterview] = useState<Interview | null>(null);
  const [rescheduleInterview, setRescheduleInterview] = useState<Interview | null>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);

  const handleSelectDate = useCallback((date: Date) => {
    setSelectedDate(date);
  }, []);

  const handleViewFeedback = useCallback((interview: Interview) => {
    setFeedbackInterview(interview);
    setShowFeedbackForm(true);
  }, []);

  const handleReschedule = useCallback((interview: Interview) => {
    setRescheduleInterview(interview);
  }, []);

  const handleFeedbackSubmit = useCallback(
    (feedback: InterviewFeedback) => {
      if (!feedbackInterview) return;
      setInterviews((prev) =>
        prev.map((i) => (i.id === feedbackInterview.id ? { ...i, feedback, status: 'completed' as const } : i))
      );
      setShowFeedbackForm(false);
      setFeedbackInterview(null);
    },
    [feedbackInterview]
  );

  const handleRescheduleConfirm = useCallback(
    (newDate: string, newStartTime: string, newEndTime: string) => {
      if (!rescheduleInterview) return;
      setInterviews((prev) =>
        prev.map((i) =>
          i.id === rescheduleInterview.id
            ? { ...i, date: newDate, startTime: newStartTime, endTime: newEndTime, status: 'rescheduled' as const }
            : i
        )
      );
      setRescheduleInterview(null);
    },
    [rescheduleInterview]
  );

  const filteredInterviews = useMemo(() => {
    if (!selectedDate) return interviews;
    const dateStr = selectedDate.toISOString().split('T')[0];
    return interviews.filter((i) => i.date === dateStr);
  }, [interviews, selectedDate]);

  const stats = useMemo(() => {
    const scheduled = interviews.filter((i) => i.status === 'scheduled').length;
    const completed = interviews.filter((i) => i.status === 'completed').length;
    const cancelled = interviews.filter((i) => i.status === 'cancelled').length;
    const rescheduled = interviews.filter((i) => i.status === 'rescheduled').length;
    return { scheduled, completed, cancelled, rescheduled, total: interviews.length };
  }, [interviews]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Interviews</h1>
              <p className="text-sm text-gray-500 mt-1">Manage and track all interview activities</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Scheduled</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">{stats.scheduled}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Completed</p>
            <p className="text-2xl font-bold text-green-600 mt-1">{stats.completed}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Rescheduled</p>
            <p className="text-2xl font-bold text-yellow-600 mt-1">{stats.rescheduled}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Cancelled</p>
            <p className="text-2xl font-bold text-red-600 mt-1">{stats.cancelled}</p>
          </div>
        </div>

        {/* Selected date filter */}
        {selectedDate && (
          <div className="mb-4 flex items-center gap-2">
            <span className="text-sm text-gray-600">
              Showing interviews for{' '}
              <span className="font-medium">{selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span>
            </span>
            <button
              onClick={() => setSelectedDate(null)}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear filter
            </button>
          </div>
        )}

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Calendar — takes 2 cols on large screens */}
          <div className="lg:col-span-2">
            <InterviewCalendar
              interviews={filteredInterviews}
              selectedDate={selectedDate}
              onSelectDate={handleSelectDate}
            />
          </div>

          {/* Upcoming list — 1 col on large screens */}
          <div className="lg:col-span-1">
            <UpcomingInterviewsList
              interviews={filteredInterviews}
              onViewFeedback={handleViewFeedback}
              onReschedule={handleReschedule}
            />
          </div>
        </div>

        {/* Feedback form — full width below */}
        {showFeedbackForm && feedbackInterview && (
          <div className="mt-6">
            <InterviewFeedbackForm
              interview={feedbackInterview}
              onSubmit={handleFeedbackSubmit}
              onCancel={() => {
                setShowFeedbackForm(false);
                setFeedbackInterview(null);
              }}
            />
          </div>
        )}
      </main>

      {/* Reschedule Modal */}
      {rescheduleInterview && (
        <RescheduleInterviewModal
          interview={rescheduleInterview}
          onConfirm={handleRescheduleConfirm}
          onClose={() => setRescheduleInterview(null)}
        />
      )}
    </div>
  );
}
