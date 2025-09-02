import React, { useMemo } from "react";

import { GoogleCalendarIcon } from "@/components";
import { getEventColor } from "@/features/calendar/utils/eventColors";
import BaseCardView from "@/features/chat/components/interface/BaseCardView";
import { CalendarItem } from "@/types/api/calendarApiTypes";
import { GoogleCalendarEvent } from "@/types/features/calendarTypes";

interface UpcomingEventsViewProps {
  onEventClick?: (event: GoogleCalendarEvent) => void;
  events: GoogleCalendarEvent[];
  isLoading: boolean;
  error?: string | null;
  calendars: CalendarItem[];
  // Connection state props
  isConnected?: boolean;
  onConnect?: (integrationId: string) => void;
}

const UpcomingEventsView: React.FC<UpcomingEventsViewProps> = ({
  onEventClick,
  events,
  isLoading,
  error,
  calendars,
  isConnected = true,
  onConnect,
}) => {
  // Filter and group upcoming events by day (next 7 days)
  const upcomingEventsByDay = useMemo(() => {
    const today = new Date();
    const eventsByDay: { [key: string]: GoogleCalendarEvent[] } = {};

    // Get events for the next 7 days
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      const dateString = date.toDateString();

      const dayEvents = events
        .filter((event) => {
          const eventStart = new Date(
            event.start.dateTime || event.start.date || "",
          );
          return eventStart.toDateString() === dateString;
        })
        .sort((a, b) => {
          const timeA = new Date(
            a.start.dateTime || a.start.date || "",
          ).getTime();
          const timeB = new Date(
            b.start.dateTime || b.start.date || "",
          ).getTime();
          return timeA - timeB;
        });

      if (dayEvents.length > 0) {
        eventsByDay[dateString] = dayEvents;
      }
    }

    return eventsByDay;
  }, [events]);

  // Format time for display
  const formatTime = (startTime: string, endTime: string) => {
    const start = new Date(startTime);
    const end = new Date(endTime);

    const formatTimeString = (date: Date) => {
      const hours = date.getHours();
      const minutes = date.getMinutes();
      const ampm = hours >= 12 ? "PM" : "AM";
      const hour12 = hours % 12 || 12;
      const minuteStr = minutes.toString().padStart(2, "0");

      if (minutes === 0) {
        return `${hour12} ${ampm}`;
      }
      return `${hour12}:${minuteStr} ${ampm}`;
    };

    const startStr = formatTimeString(start);
    const endStr = formatTimeString(end);

    // Smart formatting - show AM/PM only when needed
    if (start.getHours() < 12 && end.getHours() >= 12) {
      // Crossing from AM to PM
      return `${startStr} – ${endStr}`;
    } else if (start.getHours() >= 12 && end.getHours() >= 12) {
      // Both PM
      const startWithoutAMPM = startStr.replace(" PM", "");
      return `${startWithoutAMPM} – ${endStr}`;
    } else if (start.getHours() < 12 && end.getHours() < 12) {
      // Both AM
      const startWithoutAMPM = startStr.replace(" AM", "");
      return `${startWithoutAMPM} – ${endStr}`;
    }

    return `${startStr} – ${endStr}`;
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return "Today";
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return "Tomorrow";
    } else {
      return date.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
      });
    }
  };

  const hasEvents = Object.keys(upcomingEventsByDay).length > 0;

  return (
    <BaseCardView
      title="Upcoming events"
      icon={<GoogleCalendarIcon className="h-6 w-6 text-zinc-500" />}
      isLoading={isLoading}
      error={error}
      isEmpty={!hasEvents}
      emptyMessage="No upcoming events"
      errorMessage="Failed to load upcoming events"
      isConnected={isConnected}
      connectIntegrationId="google_calendar"
      onConnect={onConnect}
      connectButtonText="Connect Calendar"
    >
      <div className="space-y-6 p-4">
        {Object.entries(upcomingEventsByDay).map(
          ([dateString, events], index) => (
            <div key={dateString} className="flex gap-4">
              {/* Left Side - Date (20% width like 1 of 5 columns) */}
              <div className="w-1/5 flex-shrink-0">
                <div className="sticky top-0 z-10 px-2 pt-1">
                  <span
                    className={`text-sm ${index == 0 ? "text-primary" : "text-foreground-300"}`}
                  >
                    {formatDate(dateString)}
                  </span>
                </div>
              </div>

              {/* Right Side - Events (80% width like 4 of 5 columns) */}
              <div className="flex-1 space-y-2">
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="relative flex cursor-pointer items-start gap-2 rounded-lg p-2 pl-5 transition-colors hover:bg-zinc-700/30"
                    onClick={() => onEventClick?.(event)}
                    style={{
                      backgroundColor: `${getEventColor(event, calendars)}5`,
                    }}
                  >
                    {/* Colored Pill */}
                    <div className="absolute top-0 left-1 flex h-full items-center">
                      <div
                        className="mt-0.5 h-[80%] w-1 flex-shrink-0 rounded-full"
                        style={{
                          backgroundColor: getEventColor(event, calendars),
                        }}
                      />
                    </div>

                    {/* Event Details */}
                    <div className="min-w-0 flex-1">
                      {/* Title */}
                      <div className="text-base leading-tight font-medium text-white">
                        {event.summary}
                      </div>

                      {/* Time */}
                      <div className="mt-0.5 text-xs text-zinc-400">
                        {event.start.dateTime && event.end.dateTime
                          ? formatTime(event.start.dateTime, event.end.dateTime)
                          : "All day"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ),
        )}
      </div>
    </BaseCardView>
  );
};

export default UpcomingEventsView;
