// Recurrence types for calendar events
export type RecurrenceFrequency = "DAILY" | "WEEKLY" | "MONTHLY" | "YEARLY";

export interface RecurrenceRule {
  frequency: RecurrenceFrequency;
  interval?: number; // default: 1
  count?: number;
  until?: string; // ISO date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS±HH:MM)
  by_day?: string[]; // e.g., ["MO", "WE"]
  by_month_day?: number[];
  by_month?: number[];
  exclude_dates?: string[]; // YYYY-MM-DD
  include_dates?: string[]; // YYYY-MM-DD
}

export interface RecurrenceData {
  rrule: RecurrenceRule;
}
import { CalendarItem } from "@/types/api/calendarApiTypes";

export interface CalendarCardProps {
  event: GoogleCalendarEvent | CalendarEvent;
  onClick: () => void;
  calendars: CalendarItem[];
}

export interface GoogleCalendarDateTime {
  date?: string;
  dateTime?: string;
  timeZone?: string;
}

export interface CalendarChipProps {
  calendar: CalendarItem;
  selected: boolean;
  onSelect: (id: string) => void;
}

export interface CalendarSelectorProps {
  calendars: CalendarItem[];
  selectedCalendars: string[];
  onCalendarSelect: (calendarId: string) => void;
}

export interface CalendarEventDialogProps {
  event?: GoogleCalendarEvent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode?: "view" | "create";
}

export interface GoogleCalendarPerson {
  email: string;
  self?: boolean;
}

export interface BirthdayProperties {
  contact: string;
  type: "birthday";
}

export interface GoogleCalendarEvent {
  kind: string;
  etag: string;
  id: string;
  status: "confirmed" | "tentative" | "cancelled";
  htmlLink: string;
  created: string;
  updated: string;
  summary: string;
  description: string;
  creator: GoogleCalendarPerson;
  organizer: GoogleCalendarPerson;
  start: GoogleCalendarDateTime;
  end: GoogleCalendarDateTime;
  recurrence?: string[];
  transparency?: "opaque" | "transparent";
  visibility?: "default" | "public" | "private";
  iCalUID: string;
  sequence: number;
  reminders?: {
    useDefault: boolean;
  };
  birthdayProperties?: BirthdayProperties;
  eventType?:
    | "default"
    | "birthday"
    | "outOfOffice"
    | "reminder"
    | "appointment"
    | "meeting"
    | "task"
    | "holiday"
    | "work"
    | "travel"
    | "sports"
    | "concert"
    | "party"
    | "health"
    | "study"
    | "wedding";
}

export interface GoogleCalendar {
  id: string;
  summary: string;
  backgroundColor: string;
  primary: boolean;
}

export interface BaseEvent {
  summary: string;
  description: string;
  index?: string | number;
  organizer?: {
    email?: string;
  };
  calendar_id?: string;
  is_all_day?: boolean;
  recurrence?: RecurrenceData;
}

export interface TimedEvent extends BaseEvent {
  start: string;
  end: string;
}

export interface SingleTimeEvent extends BaseEvent {
  time: string;
}

export type CalendarEvent = TimedEvent | SingleTimeEvent;

export interface EventCardProps {
  event: CalendarEvent;
  isDummy?: boolean;
  onDummyAddEvent?: () => void;
}

export interface UnifiedCalendarEventsListProps {
  events: CalendarEvent[];
  isDummy?: boolean;
  onDummyAddEvent?: (index: number) => void;
  disableAnimation?: boolean;
}

export interface EventCreatePayload {
  summary: string;
  description: string;
  is_all_day: boolean;
  start?: string;
  end?: string;
  fixedTime?: boolean;
  timezone?: string;
  recurrence?: RecurrenceData;
}

// Calendar types for conversation messages
export type CalendarOptions = {
  summary: string;
  description?: string;
  start?: string;
  end?: string;
  calendar_id?: string;
  is_all_day?: boolean;
  recurrence?: RecurrenceData;
};

// Calendar event date/time structure from Google Calendar API
export type CalendarEventDateTime = {
  date?: string; // For all-day events (YYYY-MM-DD format)
  dateTime?: string; // For timed events (RFC3339 format)
  timeZone?: string; // Timezone identifier
};

export type CalendarDeleteOptions = {
  action: "delete";
  event_id: string;
  calendar_id: string;
  summary: string;
  description?: string;
  start?: CalendarEventDateTime;
  end?: CalendarEventDateTime;
  original_query: string;
};

export type CalendarEditOptions = {
  action: "edit";
  event_id: string;
  calendar_id: string;
  original_summary: string;
  original_description?: string;
  original_start?: CalendarEventDateTime;
  original_end?: CalendarEventDateTime;
  original_query: string;
  // Updated fields (optional)
  summary?: string;
  description?: string;
  start?: string;
  end?: string;
  is_all_day?: boolean;
  timezone?: string;
};

// Calendar fetch data types for streaming components
export type CalendarFetchData = {
  summary: string;
  start_time: string;
  calendar_name: string;
};

export type CalendarListFetchData = {
  name: string;
  id: string;
  description: string;
  backgroundColor?: string;
};
