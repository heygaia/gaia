import { useCallback } from "react";

import { calendarApi } from "@/features/calendar/api/calendarApi";
import { useCalendarStore } from "@/stores/calendarStore";

export const useCalendarOperations = () => {
  const {
    setCalendars,
    setEvents,
    setNextPageToken,
    setLoading,
    setError,
    clearError,
    setInitialized,
    autoSelectPrimaryCalendar,
    selectedCalendars,
  } = useCalendarStore();

  const loadCalendars = useCallback(async () => {
    setLoading("calendars", true);
    clearError("calendars");

    try {
      const calendars = await calendarApi.fetchCalendars();
      setCalendars(calendars);
      setInitialized(true);
      autoSelectPrimaryCalendar();
      return calendars;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch calendars";
      setError("calendars", errorMessage);
      setInitialized(true);
      throw error;
    } finally {
      setLoading("calendars", false);
    }
  }, [
    setCalendars,
    setLoading,
    setError,
    clearError,
    setInitialized,
    autoSelectPrimaryCalendar,
  ]);

  const loadEvents = useCallback(
    async (
      pageToken?: string | null,
      calendarIds?: string[],
      reset = false,
    ) => {
      const calendarsToUse = calendarIds || selectedCalendars;
      if (calendarsToUse.length === 0) return;

      setLoading("events", true);
      clearError("events");

      try {
        const response = await calendarApi.fetchMultipleCalendarEvents(
          calendarsToUse,
          pageToken,
        );
        setEvents(response.events, reset);
        setNextPageToken(response.nextPageToken);
        return response;
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to fetch events";
        setError("events", errorMessage);
        throw error;
      } finally {
        setLoading("events", false);
      }
    },
    [
      selectedCalendars,
      setLoading,
      setError,
      clearError,
      setEvents,
      setNextPageToken,
    ],
  );

  return {
    loadCalendars,
    loadEvents,
  };
};
