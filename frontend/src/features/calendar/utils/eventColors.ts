import { CalendarItem } from "@/types/api/calendarApiTypes";
import { GoogleCalendarEvent } from "@/types/features/calendarTypes";

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
      event.organizer?.email === cal.id || event.creator?.email === cal.id,
  );

  // Use calendar's background color if available, otherwise use a default color
  return calendar?.backgroundColor || "#00bbff"; // Google blue as fallback
};
