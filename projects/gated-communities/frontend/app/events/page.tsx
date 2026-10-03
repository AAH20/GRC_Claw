'use client';

import React, { useState, useMemo, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface EventItem {
  id: string;
  title: string;
  description: string;
  date: string; // ISO date string YYYY-MM-DD
  startTime: string; // HH:mm
  endTime: string; // HH:mm
  location: string;
  category: 'meetup' | 'workshop' | 'social' | 'conference' | 'other';
  organizer: string;
  attendeeCount: number;
  maxAttendees: number;
  isRegistered: boolean;
  imageUrl?: string;
}

interface CalendarDay {
  date: Date;
  isCurrentMonth: boolean;
  isToday: boolean;
  events: EventItem[];
}

type ViewMode = 'calendar' | 'list';

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_EVENTS: EventItem[] = [
  {
    id: '1',
    title: 'Community Kickoff Meetup',
    description:
      'Join us for the inaugural meetup of our gated community. Network with fellow members, learn about upcoming initiatives, and help shape the future of our group.',
    date: '2026-10-10',
    startTime: '18:00',
    endTime: '20:00',
    location: 'Downtown Community Center',
    category: 'meetup',
    organizer: 'Community Team',
    attendeeCount: 42,
    maxAttendees: 100,
    isRegistered: false,
  },
  {
    id: '2',
    title: 'Web3 Workshop: Smart Contracts 101',
    description:
      'A hands-on workshop covering the fundamentals of smart contract development. Bring your laptop — we will deploy our first contract together.',
    date: '2026-10-15',
    startTime: '14:00',
    endTime: '17:00',
    location: 'Tech Hub, Room 301',
    category: 'workshop',
    organizer: 'Dev Guild',
    attendeeCount: 28,
    maxAttendees: 50,
    isRegistered: true,
  },
  {
    id: '3',
    title: 'Monthly Social Mixer',
    description:
      'Casual evening of drinks and conversation. A relaxed setting to connect with community members outside of structured events.',
    date: '2026-10-20',
    startTime: '19:00',
    endTime: '22:00',
    location: 'The Rooftop Lounge',
    category: 'social',
    organizer: 'Social Committee',
    attendeeCount: 35,
    maxAttendees: 80,
    isRegistered: false,
  },
  {
    id: '4',
    title: 'Gated Communities Conference 2026',
    description:
      'Our flagship annual conference featuring talks, panels, and workshops on the future of gated communities, token-gated access, and decentralized membership.',
    date: '2026-11-05',
    startTime: '09:00',
    endTime: '18:00',
    location: 'Grand Convention Center',
    category: 'conference',
    organizer: 'Conference Committee',
    attendeeCount: 156,
    maxAttendees: 300,
    isRegistered: false,
  },
  {
    id: '5',
    title: 'Governance Proposal Review',
    description:
      'Monthly review of active governance proposals. Members are encouraged to attend, ask questions, and cast their votes.',
    date: '2026-10-28',
    startTime: '17:00',
    endTime: '18:30',
    location: 'Virtual — Discord Stage',
    category: 'other',
    organizer: 'Governance DAO',
    attendeeCount: 67,
    maxAttendees: 200,
    isRegistered: true,
  },
  {
    id: '6',
    title: 'Design Systems Workshop',
    description:
      'Learn how to build and maintain a design system for your community-facing products. Covers tokens, components, and documentation.',
    date: '2026-11-12',
    startTime: '10:00',
    endTime: '13:00',
    location: 'Creative Studio, Floor 2',
    category: 'workshop',
    organizer: 'Design Guild',
    attendeeCount: 18,
    maxAttendees: 30,
    isRegistered: false,
  },
  {
    id: '7',
    title: 'Community AMA with Founders',
    description:
      'An open ask-me-anything session with the founding team. Get insights into the roadmap, tokenomics, and community vision.',
    date: '2026-11-18',
    startTime: '16:00',
    endTime: '17:30',
    location: 'Virtual — YouTube Live',
    category: 'meetup',
    organizer: 'Founding Team',
    attendeeCount: 89,
    maxAttendees: 500,
    isRegistered: false,
  },
  {
    id: '8',
    title: 'Hackathon: Build for the Community',
    description:
      'A 48-hour hackathon focused on building tools and integrations for gated communities. Prizes for top projects.',
    date: '2026-11-25',
    startTime: '09:00',
    endTime: '21:00',
    location: 'Innovation Lab',
    category: 'conference',
    organizer: 'Hackathon Committee',
    attendeeCount: 45,
    maxAttendees: 120,
    isRegistered: false,
  },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

const CATEGORY_COLORS: Record<EventItem['category'], string> = {
  meetup: 'bg-blue-100 text-blue-800',
  workshop: 'bg-purple-100 text-purple-800',
  social: 'bg-green-100 text-green-800',
  conference: 'bg-orange-100 text-orange-800',
  other: 'bg-gray-100 text-gray-800',
};

const CATEGORY_LABELS: Record<EventItem['category'], string> = {
  meetup: 'Meetup',
  workshop: 'Workshop',
  social: 'Social',
  conference: 'Conference',
  other: 'Other',
};

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatTime(time: string): string {
  const [hours, minutes] = time.split(':').map(Number);
  const period = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;
  return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year: number, month: number): number {
  return new Date(year, month, 1).getDay();
}

// ─── Calendar Component ──────────────────────────────────────────────────────

interface CalendarProps {
  events: EventItem[];
  selectedDate: Date;
  onSelectDate: (date: Date) => void;
  onSelectEvent: (event: EventItem) => void;
}

function Calendar({ events, selectedDate, onSelectDate, onSelectEvent }: CalendarProps) {
  const [viewYear, setViewYear] = useState(selectedDate.getFullYear());
  const [viewMonth, setViewMonth] = useState(selectedDate.getMonth());

  const today = new Date();

  const calendarDays = useMemo((): CalendarDay[] => {
    const days: CalendarDay[] = [];
    const firstDay = getFirstDayOfMonth(viewYear, viewMonth);
    const daysInMonth = getDaysInMonth(viewYear, viewMonth);
    const daysInPrevMonth = getDaysInMonth(viewYear, viewMonth - 1);

    // Previous month padding
    for (let i = firstDay - 1; i >= 0; i--) {
      const date = new Date(viewYear, viewMonth - 1, daysInPrevMonth - i);
      days.push({
        date,
        isCurrentMonth: false,
        isToday: isSameDay(date, today),
        events: events.filter((e) => isSameDay(new Date(e.date + 'T00:00:00'), date)),
      });
    }

    // Current month
    for (let i = 1; i <= daysInMonth; i++) {
      const date = new Date(viewYear, viewMonth, i);
      days.push({
        date,
        isCurrentMonth: true,
        isToday: isSameDay(date, today),
        events: events.filter((e) => isSameDay(new Date(e.date + 'T00:00:00'), date)),
      });
    }

    // Next month padding
    const remaining = 42 - days.length;
    for (let i = 1; i <= remaining; i++) {
      const date = new Date(viewYear, viewMonth + 1, i);
      days.push({
        date,
        isCurrentMonth: false,
        isToday: isSameDay(date, today),
        events: events.filter((e) => isSameDay(new Date(e.date + 'T00:00:00'), date)),
      });
    }

    return days;
  }, [viewYear, viewMonth, events]);

  const goToPrevMonth = () => {
    if (viewMonth === 0) {
      setViewYear(viewYear - 1);
      setViewMonth(11);
    } else {
      setViewMonth(viewMonth - 1);
    }
  };

  const goToNextMonth = () => {
    if (viewMonth === 11) {
      setViewYear(viewYear + 1);
      setViewMonth(0);
    } else {
      setViewMonth(viewMonth + 1);
    }
  };

  const goToToday = () => {
    setViewYear(today.getFullYear());
    setViewMonth(today.getMonth());
    onSelectDate(today);
  };

  const monthLabel = new Date(viewYear, viewMonth, 1).toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  });

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Calendar Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">{monthLabel}</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={goToToday}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Today
          </button>
          <button
            onClick={goToPrevMonth}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Previous month"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            onClick={goToNextMonth}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Next month"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Weekday Headers */}
      <div className="grid grid-cols-7 border-b border-gray-200">
        {weekDays.map((day) => (
          <div
            key={day}
            className="px-2 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7">
        {calendarDays.map((day, idx) => {
          const isSelected = isSameDay(day.date, selectedDate);
          return (
            <button
              key={idx}
              onClick={() => onSelectDate(day.date)}
              className={`
                relative min-h-[80px] md:min-h-[100px] p-1.5 md:p-2 text-left border-b border-r border-gray-100 transition-colors
                ${!day.isCurrentMonth ? 'bg-gray-50 text-gray-400' : 'text-gray-900 hover:bg-gray-50'}
                ${isSelected ? 'bg-blue-50 ring-2 ring-inset ring-blue-500' : ''}
              `}
            >
              <span
                className={`
                  inline-flex items-center justify-center w-7 h-7 text-sm rounded-full
                  ${day.isToday ? 'bg-blue-600 text-white font-bold' : ''}
                  ${isSelected && !day.isToday ? 'bg-blue-100 text-blue-700 font-semibold' : ''}
                `}
              >
                {day.date.getDate()}
              </span>
              {/* Event indicators */}
              <div className="mt-1 space-y-0.5">
                {day.events.slice(0, 2).map((event) => (
                  <button
                    key={event.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectEvent(event);
                    }}
                    className="block w-full text-left px-1.5 py-0.5 text-xs rounded truncate bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
                  >
                    {event.title}
                  </button>
                ))}
                {day.events.length > 2 && (
                  <span className="block text-xs text-gray-500 px-1.5">
                    +{day.events.length - 2} more
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Event List Component ────────────────────────────────────────────────────

interface EventListProps {
  events: EventItem[];
  onSelectEvent: (event: EventItem) => void;
}

function EventList({ events, onSelectEvent }: EventListProps) {
  const sortedEvents = useMemo(
    () => [...events].sort((a, b) => a.date.localeCompare(b.date)),
    [events]
  );

  if (sortedEvents.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
        <svg
          className="mx-auto w-12 h-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900">No upcoming events</h3>
        <p className="mt-2 text-sm text-gray-500">
          There are no events scheduled. Create one to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sortedEvents.map((event) => (
        <button
          key={event.id}
          onClick={() => onSelectEvent(event)}
          className="w-full text-left bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md hover:border-gray-300 transition-all group"
        >
          <div className="flex flex-col sm:flex-row sm:items-start gap-4">
            {/* Date Badge */}
            <div className="flex-shrink-0 w-14 h-14 bg-blue-50 rounded-lg flex flex-col items-center justify-center">
              <span className="text-xs font-medium text-blue-600 uppercase">
                {new Date(event.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short' })}
              </span>
              <span className="text-xl font-bold text-blue-700">
                {new Date(event.date + 'T00:00:00').getDate()}
              </span>
            </div>

            {/* Event Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate">
                  {event.title}
                </h3>
                <span
                  className={`flex-shrink-0 px-2.5 py-0.5 text-xs font-medium rounded-full ${CATEGORY_COLORS[event.category]}`}
                >
                  {CATEGORY_LABELS[event.category]}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-600 line-clamp-2">{event.description}</p>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500">
                <span className="inline-flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  {formatTime(event.startTime)} – {formatTime(event.endTime)}
                </span>
                <span className="inline-flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  {event.location}
                </span>
                <span className="inline-flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                    />
                  </svg>
                  {event.attendeeCount}/{event.maxAttendees} attending
                </span>
              </div>
            </div>

            {/* Arrow */}
            <div className="hidden sm:flex items-center self-center">
              <svg
                className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

// ─── Event Detail Modal ──────────────────────────────────────────────────────

interface EventDetailModalProps {
  event: EventItem | null;
  onClose: () => void;
  onRegister: (eventId: string) => void;
}

function EventDetailModal({ event, onClose, onRegister }: EventDetailModalProps) {
  if (!event) return null;

  const spotsLeft = event.maxAttendees - event.attendeeCount;
  const isFull = spotsLeft <= 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors z-10"
          aria-label="Close"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-gray-100">
          <span
            className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${CATEGORY_COLORS[event.category]}`}
          >
            {CATEGORY_LABELS[event.category]}
          </span>
          <h2 className="mt-3 text-2xl font-bold text-gray-900">{event.title}</h2>
          <p className="mt-1 text-sm text-gray-500">Organized by {event.organizer}</p>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5">
          {/* Date & Time */}
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{formatDate(event.date)}</p>
              <p className="text-sm text-gray-500">
                {formatTime(event.startTime)} – {formatTime(event.endTime)}
              </p>
            </div>
          </div>

          {/* Location */}
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{event.location}</p>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">About this event</h3>
            <p className="text-sm text-gray-600 leading-relaxed">{event.description}</p>
          </div>

          {/* Attendance */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-900">Attendance</h3>
              <span className="text-sm text-gray-500">
                {event.attendeeCount}/{event.maxAttendees} registered
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all"
                style={{ width: `${Math.min((event.attendeeCount / event.maxAttendees) * 100, 100)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              {isFull ? 'This event is full' : `${spotsLeft} spots remaining`}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 rounded-b-2xl">
          {event.isRegistered ? (
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2 text-sm font-medium text-green-700">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                You&apos;re registered
              </span>
              <button
                onClick={() => onRegister(event.id)}
                className="px-4 py-2 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
              >
                Cancel registration
              </button>
            </div>
          ) : (
            <button
              onClick={() => onRegister(event.id)}
              disabled={isFull}
              className={`
                w-full py-3 text-sm font-semibold rounded-lg transition-colors
                ${
                  isFull
                    ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }
              `}
            >
              {isFull ? 'Event Full' : 'Register for Event'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Create Event Form ────────────────────────────────────────────────────────

interface CreateEventFormProps {
  onClose: () => void;
  onSubmit: (event: Omit<EventItem, 'id' | 'attendeeCount' | 'isRegistered'>) => void;
}

function CreateEventForm({ onClose, onSubmit }: CreateEventFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('18:00');
  const [endTime, setEndTime] = useState('20:00');
  const [location, setLocation] = useState('');
  const [category, setCategory] = useState<EventItem['category']>('meetup');
  const [organizer, setOrganizer] = useState('');
  const [maxAttendees, setMaxAttendees] = useState(50);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!title.trim()) newErrors.title = 'Title is required';
    if (!description.trim()) newErrors.description = 'Description is required';
    if (!date) newErrors.date = 'Date is required';
    if (!startTime) newErrors.startTime = 'Start time is required';
    if (!endTime) newErrors.endTime = 'End time is required';
    if (startTime && endTime && startTime >= endTime)
      newErrors.endTime = 'End time must be after start time';
    if (!location.trim()) newErrors.location = 'Location is required';
    if (!organizer.trim()) newErrors.organizer = 'Organizer is required';
    if (maxAttendees < 1) newErrors.maxAttendees = 'Must have at least 1 attendee';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({
      title: title.trim(),
      description: description.trim(),
      date,
      startTime,
      endTime,
      location: location.trim(),
      category,
      organizer: organizer.trim(),
      maxAttendees,
    });
  };

  const inputClass = (field: string) =>
    `w-full px-4 py-2.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
      errors[field] ? 'border-red-300 bg-red-50' : 'border-gray-300'
    }`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white px-6 pt-6 pb-4 border-b border-gray-100 flex items-center justify-between rounded-t-2xl z-10">
          <h2 className="text-xl font-bold text-gray-900">Create New Event</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-5">
          {/* Title */}
          <div>
            <label htmlFor="event-title" className="block text-sm font-medium text-gray-700 mb-1.5">
              Event Title <span className="text-red-500">*</span>
            </label>
            <input
              id="event-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Community Meetup"
              className={inputClass('title')}
            />
            {errors.title && <p className="mt-1 text-xs text-red-600">{errors.title}</p>}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="event-desc" className="block text-sm font-medium text-gray-700 mb-1.5">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="event-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your event..."
              rows={3}
              className={inputClass('description')}
            />
            {errors.description && <p className="mt-1 text-xs text-red-600">{errors.description}</p>}
          </div>

          {/* Date & Time */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label htmlFor="event-date" className="block text-sm font-medium text-gray-700 mb-1.5">
                Date <span className="text-red-500">*</span>
              </label>
              <input
                id="event-date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className={inputClass('date')}
              />
              {errors.date && <p className="mt-1 text-xs text-red-600">{errors.date}</p>}
            </div>
            <div>
              <label htmlFor="event-start" className="block text-sm font-medium text-gray-700 mb-1.5">
                Start Time <span className="text-red-500">*</span>
              </label>
              <input
                id="event-start"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className={inputClass('startTime')}
              />
              {errors.startTime && <p className="mt-1 text-xs text-red-600">{errors.startTime}</p>}
            </div>
            <div>
              <label htmlFor="event-end" className="block text-sm font-medium text-gray-700 mb-1.5">
                End Time <span className="text-red-500">*</span>
              </label>
              <input
                id="event-end"
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className={inputClass('endTime')}
              />
              {errors.endTime && <p className="mt-1 text-xs text-red-600">{errors.endTime}</p>}
            </div>
          </div>

          {/* Location */}
          <div>
            <label htmlFor="event-location" className="block text-sm font-medium text-gray-700 mb-1.5">
              Location <span className="text-red-500">*</span>
            </label>
            <input
              id="event-location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g., Community Center or Virtual"
              className={inputClass('location')}
            />
            {errors.location && <p className="mt-1 text-xs text-red-600">{errors.location}</p>}
          </div>

          {/* Category & Organizer */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="event-category" className="block text-sm font-medium text-gray-700 mb-1.5">
                Category
              </label>
              <select
                id="event-category"
                value={category}
                onChange={(e) => setCategory(e.target.value as EventItem['category'])}
                className={inputClass('category')}
              >
                <option value="meetup">Meetup</option>
                <option value="workshop">Workshop</option>
                <option value="social">Social</option>
                <option value="conference">Conference</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label htmlFor="event-organizer" className="block text-sm font-medium text-gray-700 mb-1.5">
                Organizer <span className="text-red-500">*</span>
              </label>
              <input
                id="event-organizer"
                type="text"
                value={organizer}
                onChange={(e) => setOrganizer(e.target.value)}
                placeholder="e.g., Community Team"
                className={inputClass('organizer')}
              />
              {errors.organizer && <p className="mt-1 text-xs text-red-600">{errors.organizer}</p>}
            </div>
          </div>

          {/* Max Attendees */}
          <div>
            <label htmlFor="event-max" className="block text-sm font-medium text-gray-700 mb-1.5">
              Max Attendees
            </label>
            <input
              id="event-max"
              type="number"
              value={maxAttendees}
              onChange={(e) => setMaxAttendees(parseInt(e.target.value, 10) || 0)}
              min={1}
              className={inputClass('maxAttendees')}
            />
            {errors.maxAttendees && <p className="mt-1 text-xs text-red-600">{errors.maxAttendees}</p>}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Create Event
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>(MOCK_EVENTS);
  const [viewMode, setViewMode] = useState<ViewMode>('calendar');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<EventItem['category'] | 'all'>('all');

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const matchesSearch =
        searchQuery === '' ||
        event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        event.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        event.location.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = categoryFilter === 'all' || event.category === categoryFilter;
      return matchesSearch && matchesCategory;
    });
  }, [events, searchQuery, categoryFilter]);

  const upcomingEvents = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return filteredEvents
      .filter((e) => new Date(e.date + 'T00:00:00') >= today)
      .sort((a, b) => a.date.localeCompare(b.date));
  }, [filteredEvents]);

  const handleSelectDate = useCallback((date: Date) => {
    setSelectedDate(date);
  }, []);

  const handleSelectEvent = useCallback((event: EventItem) => {
    setSelectedEvent(event);
  }, []);

  const handleRegister = useCallback((eventId: string) => {
    setEvents((prev) =>
      prev.map((e) => {
        if (e.id !== eventId) return e;
        const isRegistered = !e.isRegistered;
        return {
          ...e,
          isRegistered,
          attendeeCount: isRegistered ? e.attendeeCount + 1 : e.attendeeCount - 1,
        };
      })
    );
    setSelectedEvent((prev) => {
      if (!prev || prev.id !== eventId) return prev;
      const isRegistered = !prev.isRegistered;
      return {
        ...prev,
        isRegistered,
        attendeeCount: isRegistered ? prev.attendeeCount + 1 : prev.attendeeCount - 1,
      };
    });
  }, []);

  const handleCreateEvent = useCallback(
    (eventData: Omit<EventItem, 'id' | 'attendeeCount' | 'isRegistered'>) => {
      const newEvent: EventItem = {
        ...eventData,
        id: Date.now().toString(),
        attendeeCount: 0,
        isRegistered: false,
      };
      setEvents((prev) => [...prev, newEvent]);
      setShowCreateForm(false);
    },
    []
  );

  const eventsOnSelectedDate = useMemo(() => {
    return filteredEvents.filter((e) =>
      isSameDay(new Date(e.date + 'T00:00:00'), selectedDate)
    );
  }, [filteredEvents, selectedDate]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Events</h1>
              <p className="mt-1 text-sm text-gray-500">
                Discover and join community events
              </p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors self-start sm:self-auto"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Event
            </button>
          </div>

          {/* Filters */}
          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            {/* Search */}
            <div className="relative flex-1">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search events..."
                className="w-full pl-10 pr-4 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Category Filter */}
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as EventItem['category'] | 'all')}
              className="px-4 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            >
              <option value="all">All Categories</option>
              <option value="meetup">Meetup</option>
              <option value="workshop">Workshop</option>
              <option value="social">Social</option>
              <option value="conference">Conference</option>
              <option value="other">Other</option>
            </select>

            {/* View Toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('calendar')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'calendar'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'list'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 10h16M4 14h16M4 18h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Calendar / List View */}
          <div className="lg:col-span-2">
            {viewMode === 'calendar' ? (
              <Calendar
                events={filteredEvents}
                selectedDate={selectedDate}
                onSelectDate={handleSelectDate}
                onSelectEvent={handleSelectEvent}
              />
            ) : (
              <EventList events={upcomingEvents} onSelectEvent={handleSelectEvent} />
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Selected Date Events */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                {viewMode === 'calendar'
                  ? `Events on ${selectedDate.toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric',
                    })}`
                  : 'Upcoming Events'}
              </h3>
              {viewMode === 'calendar' ? (
                eventsOnSelectedDate.length > 0 ? (
                  <div className="space-y-3">
                    {eventsOnSelectedDate.map((event) => (
                      <button
                        key={event.id}
                        onClick={() => handleSelectEvent(event)}
                        className="w-full text-left p-3 rounded-lg bg-gray-50 hover:bg-blue-50 transition-colors group"
                      >
                        <p className="text-sm font-medium text-gray-900 group-hover:text-blue-700 truncate">
                          {event.title}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {formatTime(event.startTime)} – {formatTime(event.endTime)}
                        </p>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No events on this date</p>
                )
              ) : (
                <div className="space-y-3">
                  {upcomingEvents.slice(0, 5).map((event) => (
                    <button
                      key={event.id}
                      onClick={() => handleSelectEvent(event)}
                      className="w-full text-left p-3 rounded-lg bg-gray-50 hover:bg-blue-50 transition-colors group"
                    >
                      <p className="text-sm font-medium text-gray-900 group-hover:text-blue-700 truncate">
                        {event.title}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {formatDate(event.date)} · {formatTime(event.startTime)}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Stats */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Stats</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-700">{events.length}</p>
                  <p className="text-xs text-blue-600 mt-0.5">Total Events</p>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-700">{upcomingEvents.length}</p>
                  <p className="text-xs text-green-600 mt-0.5">Upcoming</p>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <p className="text-2xl font-bold text-purple-700">
                    {events.filter((e) => e.isRegistered).length}
                  </p>
                  <p className="text-xs text-purple-600 mt-0.5">Registered</p>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <p className="text-2xl font-bold text-orange-700">
                    {new Set(events.map((e) => e.organizer)).size}
                  </p>
                  <p className="text-xs text-orange-600 mt-0.5">Organizers</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Event Detail Modal */}
      <EventDetailModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
        onRegister={handleRegister}
      />

      {/* Create Event Form */}
      {showCreateForm && (
        <CreateEventForm onClose={() => setShowCreateForm(false)} onSubmit={handleCreateEvent} />
      )}
    </div>
  );
}
