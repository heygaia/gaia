import { create } from "zustand";

import { calendarApi } from "@/features/calendar/api/calendarApi";
import { CalendarItem } from "@/types/api/calendarApiTypes";
import { GoogleCalendarEvent } from "@/types/features/calendarTypes";

interface CalendarState {
  calendars: CalendarItem[];
  selectedCalendars: string[];
  events: GoogleCalendarEvent[];
  nextPageToken: string | null;
  loading: {
    calendars: boolean;
    events: boolean;
  };
  error: {
    calendars: string | null;
    events: string | null;
  };
  isInitialized: boolean;

  setSelectedCalendars: (calendarIds: string[]) => void;
  toggleCalendarSelection: (calendarId: string) => void;
  resetEvents: () => void;
  clearCalendarError: (type: "calendars" | "events") => void;
  initializeFromStorage: () => void;
  fetchCalendars: () => Promise<void>;
  fetchEvents: (params: {
    pageToken?: string | null;
    calendarIds: string[];
    reset?: boolean;
  }) => Promise<void>;
}

export const useCalendarStore = create<CalendarState>((set, get) => ({
  calendars: [],
  selectedCalendars: [],
  events: [],
  nextPageToken: null,
  loading: {
    calendars: false,
    events: false,
  },
  error: {
    calendars: null,
    events: null,
  },
  isInitialized: false,

  setSelectedCalendars: (calendarIds: string[]) => {
    set({ selectedCalendars: calendarIds });
    if (typeof window !== "undefined") {
      localStorage.setItem("selectedCalendars", JSON.stringify(calendarIds));
    }
  },

  toggleCalendarSelection: (calendarId: string) => {
    set((state) => {
      const index = state.selectedCalendars.indexOf(calendarId);
      const newSelected =
        index === -1
          ? [...state.selectedCalendars, calendarId]
          : state.selectedCalendars.filter((id) => id !== calendarId);

      if (typeof window !== "undefined") {
        localStorage.setItem("selectedCalendars", JSON.stringify(newSelected));
      }

      return { selectedCalendars: newSelected };
    });
  },

  resetEvents: () =>
    set({
      events: [],
      nextPageToken: null,
      error: { ...get().error, events: null },
    }),

  clearCalendarError: (type: "calendars" | "events") =>
    set((state) => ({
      error: { ...state.error, [type]: null },
    })),

  initializeFromStorage: () => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("selectedCalendars");
      if (saved) {
        try {
          const selectedCalendars = JSON.parse(saved);
          set({ selectedCalendars });
        } catch {
          // Invalid JSON, ignore
        }
      }
    }
  },

  fetchCalendars: async () => {
    set((state) => ({
      loading: { ...state.loading, calendars: true },
      error: { ...state.error, calendars: null },
    }));

    try {
      const calendars = await calendarApi.fetchCalendars();

      set((state) => {
        let selectedCalendars = state.selectedCalendars;

        // Auto-select calendars if none selected and we have calendars
        if (state.selectedCalendars.length === 0 && calendars.length > 0) {
          const primaryCalendar = calendars.find((cal) => cal.primary);
          if (primaryCalendar) {
            selectedCalendars = [primaryCalendar.id];
            if (typeof window !== "undefined") {
              localStorage.setItem(
                "selectedCalendars",
                JSON.stringify([primaryCalendar.id]),
              );
            }
          }
        }

        return {
          calendars,
          selectedCalendars,
          loading: { ...state.loading, calendars: false },
          isInitialized: true,
        };
      });
    } catch (error) {
      set((state) => ({
        loading: { ...state.loading, calendars: false },
        error: {
          ...state.error,
          calendars:
            error instanceof Error
              ? error.message
              : "Failed to fetch calendars",
        },
        isInitialized: true,
      }));
    }
  },

  fetchEvents: async ({ pageToken, calendarIds, reset = false }) => {
    set((state) => ({
      loading: { ...state.loading, events: true },
      error: { ...state.error, events: null },
    }));

    try {
      const response = await calendarApi.fetchMultipleCalendarEvents(
        calendarIds,
        pageToken,
      );

      set((state) => ({
        loading: { ...state.loading, events: false },
        events: reset ? response.events : [...state.events, ...response.events],
        nextPageToken: response.nextPageToken,
      }));
    } catch (error) {
      set((state) => ({
        loading: { ...state.loading, events: false },
        error: {
          ...state.error,
          events:
            error instanceof Error ? error.message : "Failed to fetch events",
        },
      }));
    }
  },
}));
