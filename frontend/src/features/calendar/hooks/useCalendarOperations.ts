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
      customStartDate?: Date,
      customEndDate?: Date,
    ) => {
      const calendarsToUse = calendarIds || selectedCalendars;
      if (calendarsToUse.length === 0) return;

      setLoading("events", true);
      clearError("events");

      try {
        let startDate: Date;
        let endDate: Date;

        if (customStartDate && customEndDate) {
          // Use provided custom date range
          startDate = customStartDate;
          endDate = customEndDate;
        } else {
          // Use default 3-month rolling window: 1 month past to 2 months future
          const now = new Date();
          startDate = new Date(now);
          startDate.setMonth(startDate.getMonth() - 1);
          startDate.setDate(1); // Start of month

          endDate = new Date(now);
          endDate.setMonth(endDate.getMonth() + 2);
          endDate.setDate(0); // End of month
        }

        // Format dates as YYYY-MM-DD
        const formatDate = (date: Date) => date.toISOString().split("T")[0];

        const response = await calendarApi.fetchMultipleCalendarEvents(
          calendarsToUse,
          pageToken,
          formatDate(startDate),
          formatDate(endDate),
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
