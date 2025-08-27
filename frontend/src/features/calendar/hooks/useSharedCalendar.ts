"use client";

import { useCallback, useEffect } from "react";

import { useCalendarStore } from "@/stores/calendarStore";

export const useSharedCalendar = () => {
  const store = useCalendarStore();

  // Initialize from localStorage on mount
  useEffect(() => {
    store.initializeFromStorage();
  }, [store]);

  // Load calendars
  const loadCalendars = useCallback(async () => {
    return store.fetchCalendars();
  }, [store]);

  // Load events
  const loadEvents = useCallback(
    async (
      pageToken?: string | null,
      calendarIds?: string[],
      reset = false,
    ) => {
      const calendarsToUse = calendarIds || store.selectedCalendars;
      if (calendarsToUse.length === 0) return;

      return store.fetchEvents({
        pageToken,
        calendarIds: calendarsToUse,
        reset,
      });
    },
    [store],
  );

  // Clear events
  const clearEvents = useCallback(() => {
    store.resetEvents();
  }, [store]);

  // Handle calendar selection
  const handleCalendarSelect = useCallback(
    (calendarId: string) => {
      store.toggleCalendarSelection(calendarId);
    },
    [store],
  );

  // Set selected calendars (bulk operation)
  const setSelectedCalendars = useCallback(
    (calendarIds: string[]) => {
      store.setSelectedCalendars(calendarIds);
    },
    [store],
  );

  // Clear errors
  const clearError = useCallback(
    (errorType: "calendars" | "events") => {
      store.clearCalendarError(errorType);
    },
    [store],
  );

  return {
    // State
    calendars: store.calendars,
    selectedCalendars: store.selectedCalendars,
    events: store.events,
    nextPageToken: store.nextPageToken,
    loading: store.loading,
    error: store.error,
    isInitialized: store.isInitialized,

    // Actions
    loadCalendars,
    loadEvents,
    clearEvents,
    handleCalendarSelect,
    setSelectedCalendars,
    clearError,
  };
};
