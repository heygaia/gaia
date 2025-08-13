import { GoogleCalendarEvent } from "@/types/features/calendarTypes";
import { CalendarItem } from "@/types/api/calendarApiTypes";

// Helper function to get event color dynamically
export const getEventColor = (
  event: GoogleCalendarEvent,
  calendars: CalendarItem[],
) => {
  // Find the calendar this event belongs to
  const calendar = calendars.find(
    (cal) =>
      // Events don't always have organizer.email matching calendar id,
      // so we'll use a fallback color scheme
      event.organizer?.email === cal.id ||
      event.creator?.email === cal.id ||
      // Also try to match by calendar id if available
      (event as any).calendarId === cal.id,
  );

  // Use calendar's background color if available, otherwise use a default color
  return calendar?.backgroundColor || "#4285f4"; // Google blue as fallback
};
