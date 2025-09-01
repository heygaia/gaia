"use client";

import { useCallback } from "react";

import { useCalendarStore } from "@/stores/calendarStore";

import { useCalendarOperations } from "./useCalendarOperations";

export const useSharedCalendar = () => {
  const {
    calendars,
    selectedCalendars,
    events,
    nextPageToken,
    loading,
    error,
    isInitialized,
    setSelectedCalendars,
    toggleCalendarSelection,
    resetEvents,
    clearError,
  } = useCalendarStore();

  const { loadCalendars, loadEvents } = useCalendarOperations();

  // Handle calendar selection
  const handleCalendarSelect = useCallback(
    (calendarId: string) => {
      toggleCalendarSelection(calendarId);
    },
    [toggleCalendarSelection],
  );

  // Clear events
  const clearEvents = useCallback(() => {
    resetEvents();
  }, [resetEvents]);

  return {
    // State
    calendars,
    selectedCalendars,
    events,
    nextPageToken,
    loading,
    error,
    isInitialized,

    // Actions
    loadCalendars,
    loadEvents,
    clearEvents,
    handleCalendarSelect,
    setSelectedCalendars,
    clearError,
  };
};
