import { toast } from "sonner";

import { apiService } from "@/lib/api";
import {
  CalendarEventsResponse,
  CalendarItem,
} from "@/types/api/calendarApiTypes";
import {
  EventCreatePayload,
  GoogleCalendar,
  GoogleCalendarEvent,
} from "@/types/features/calendarTypes";

export const calendarApi = {
  // Fetch calendar events for specific calendar
  fetchCalendarEvents: async (
    calendarId: string,
    pageToken?: string | null,
  ): Promise<CalendarEventsResponse> => {
    // Build URL with query parameters
    const params = new URLSearchParams();
    if (pageToken) params.append("page_token", pageToken);
    const url = `/calendar/${calendarId}/events${params.toString() ? `?${params.toString()}` : ""}`;

    return apiService.get<CalendarEventsResponse>(url, {
      silent: true, // Silent to avoid toasts for internal operations
    });
  },

  // Fetch events from multiple calendars
  fetchMultipleCalendarEvents: async (
    calendarIds: string[],
    pageToken?: string | null,
  ): Promise<CalendarEventsResponse> => {
    try {
      if (!calendarIds?.length) {
        toast.error("No calendars selected");
        return { events: [], nextPageToken: null };
      }

      // Only show loading toast for initial fetch (no pageToken)
      if (!pageToken) {
        toast.loading("Fetching Events...", { id: "fetching" });
      }

      const allEvents: GoogleCalendarEvent[] = [];

      for (const calendarId of calendarIds) {
        try {
          const response = await calendarApi.fetchCalendarEvents(
            calendarId,
            pageToken,
          );
          allEvents.push(...response.events);
        } catch (err) {
          console.error(
            `Failed to fetch events for calendar ${calendarId}:`,
            err,
          );
        }
      }

      toast.dismiss("fetching");
      // Disable pagination for multiple calendars to prevent infinite fetching
      // Each calendar has its own pagination token, using one token for all doesn't work
      return { events: allEvents, nextPageToken: null };
    } catch (error) {
      toast.dismiss("fetching");
      toast.error("Failed to fetch calendar events");
      console.error("Error in fetchMultipleCalendarEvents:", error);
      throw error;
    }
  },

  // Fetch available calendars
  fetchCalendars: async (): Promise<CalendarItem[]> => {
    const response = await apiService.get<{ items: GoogleCalendar[] }>(
      "/calendar/list",
    );

    // Map Google Calendar API response to our Calendar type
    return response.items.map((item) => ({
      id: item.id,
      name: item.summary,
      summary: item.summary,
      backgroundColor: item.backgroundColor,
      primary: item.primary || false,
    }));
  },

  // Create a new calendar event
  createEvent: async (
    calendarId: string,
    event: Partial<GoogleCalendarEvent>,
  ): Promise<GoogleCalendarEvent> => {
    return apiService.post<GoogleCalendarEvent>(
      `/calendar/${calendarId}/events`,
      event,
      {
        successMessage: "Event created successfully",
        errorMessage: "Failed to create event",
      },
    );
  },

  // Update a calendar event
  updateEvent: async (
    calendarId: string,
    eventId: string,
    event: Partial<GoogleCalendarEvent>,
  ): Promise<GoogleCalendarEvent> => {
    return apiService.put<GoogleCalendarEvent>(
      `/calendar/${calendarId}/events/${eventId}`,
      event,
      {
        successMessage: "Event updated successfully",
        errorMessage: "Failed to update event",
      },
    );
  },

  // Delete a calendar event
  deleteEvent: async (calendarId: string, eventId: string): Promise<void> => {
    return apiService.delete(`/calendar/${calendarId}/events/${eventId}`, {
      successMessage: "Event deleted successfully",
      errorMessage: "Failed to delete event",
    });
  },

  // Fetch calendar list (alias for fetchCalendars)
  fetchCalendarList: async (): Promise<GoogleCalendar[]> => {
    const calendars = await calendarApi.fetchCalendars();
    return calendars.map((cal) => ({
      id: cal.id,
      summary: cal.name || cal.summary || "",
      backgroundColor: cal.backgroundColor || "#4285F4",
      primary: cal.primary || false,
    }));
  },

  // Fetch calendar preferences
  fetchCalendarPreferences: async (): Promise<string[]> => {
    try {
      const data = await apiService.get<{
        selected_calendars?: string[];
        calendar_ids?: string[];
      }>("/calendar/preferences", { silent: true });
      return data.selected_calendars || data.calendar_ids || [];
    } catch (error) {
      console.error("Error fetching calendar preferences:", error);
      return [];
    }
  },

  // Update calendar preferences
  updateCalendarPreferences: async (calendarIds: string[]): Promise<void> => {
    return apiService.put(
      "/calendar/preferences",
      { selected_calendars: calendarIds },
      {
        silent: true,
      },
    );
  },

  // Create event without specifying calendar ID (uses default calendar)
  createEventDefault: async (
    event: EventCreatePayload,
  ): Promise<GoogleCalendarEvent> => {
    return apiService.post<GoogleCalendarEvent>("/calendar/event", event, {
      successMessage: "Event added to calendar!",
      errorMessage: "Failed to add event",
    });
  },

  // Delete event via agent tool (unified endpoint)
  deleteEventByAgent: async (deletePayload: {
    event_id: string;
    calendar_id: string;
    summary?: string;
  }): Promise<{ success: boolean; message: string }> => {
    return apiService.delete<{ success: boolean; message: string }>(
      "/calendar/event",
      deletePayload,
      {
        successMessage: "Event deleted successfully!",
        errorMessage: "Failed to delete event",
      },
    );
  },

  // Update event via agent tool (unified endpoint)
  updateEventByAgent: async (updatePayload: {
    event_id: string;
    calendar_id: string;
    summary?: string;
    description?: string;
    start?: string;
    end?: string;
    is_all_day?: boolean;
    timezone?: string;
    original_summary?: string;
  }): Promise<GoogleCalendarEvent> => {
    return apiService.put<GoogleCalendarEvent>(
      "/calendar/event",
      updatePayload,
      {
        successMessage: "Event updated successfully!",
        errorMessage: "Failed to update event",
      },
    );
  },
};
