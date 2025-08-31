import { useQuery, UseQueryOptions } from "@tanstack/react-query";

import { apiService } from "@/lib/api";
import { GoogleCalendarEvent } from "@/types/features/calendarTypes";

interface CalendarEventsResponse {
  events: GoogleCalendarEvent[];
  nextPageToken?: string;
}

/**
 * React Query hook for fetching upcoming calendar events with 5-minute caching
 */
export const useUpcomingEventsQuery = (
  maxResults: number = 10,
  options?: Partial<UseQueryOptions<GoogleCalendarEvent[], Error>>,
) => {
  return useQuery({
    queryKey: ["upcoming-events", maxResults],
    queryFn: async (): Promise<GoogleCalendarEvent[]> => {
      const response = await apiService.get<CalendarEventsResponse>(
        `/calendar/events?max_results=${maxResults}`,
        {
          errorMessage: "Failed to fetch calendar events",
          silent: true,
        },
      );
      return response.events || [];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - data stays fresh
    gcTime: 10 * 60 * 1000, // 10 minutes - cache persistence
    retry: 2,
    refetchOnWindowFocus: false, // Don't refetch on window focus for dashboard
    ...options,
  });
};
