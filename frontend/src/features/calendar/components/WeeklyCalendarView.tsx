"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";

import { useSharedCalendar } from "@/features/calendar/hooks/useSharedCalendar";
import { GoogleCalendarEvent } from "@/types/features/calendarTypes";

interface EventPosition {
  event: GoogleCalendarEvent;
  top: number;
  height: number;
  left: number;
  width: number;
}

interface WeeklyCalendarViewProps {
  onEventClick?: (event: GoogleCalendarEvent) => void;
}

const WeeklyCalendarView: React.FC<WeeklyCalendarViewProps> = ({
  onEventClick,
}) => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const dateStripRef = useRef<HTMLDivElement>(null);

  const {
    events,
    loading,
    error,
    calendars,
    selectedCalendars,
    isInitialized,
    loadCalendars,
    loadEvents,
    clearEvents,
  } = useSharedCalendar();

  // Initialize calendars on mount
  useEffect(() => {
    if (!isInitialized && !loading.calendars) {
      loadCalendars();
    }
  }, [isInitialized, loading.calendars, loadCalendars]);

  // Fetch events when selected calendars change or when calendars are first loaded
  useEffect(() => {
    if (selectedCalendars.length > 0 && isInitialized) {
      loadEvents(null, selectedCalendars, true);
    }
  }, [selectedCalendars, isInitialized, loadEvents]);

  // Generate hours from 12AM to 11PM for a full day view (24 hours)
  const hours = useMemo(() => {
    return Array.from({ length: 24 }, (_, i) => i); // 12AM to 11PM (0-23)
  }, []);

  // Get extended date range for horizontal scrolling (show 2 weeks before and after)
  const extendedDates = useMemo(() => {
    const startOfWeek = new Date(currentWeek);
    const day = startOfWeek.getDay();
    startOfWeek.setDate(startOfWeek.getDate() - day - 14); // Go 2 weeks before Sunday

    return Array.from({ length: 35 }, (_, i) => {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      return date;
    });
  }, [currentWeek]);

  // Helper function to get event color
  const getEventColor = (event: GoogleCalendarEvent) => {
    // Find the calendar this event belongs to
    const calendar = calendars.find(
      (cal) =>
        // Events don't always have organizer.email matching calendar id,
        // so we'll use a fallback color scheme
        event.organizer?.email === cal.id || event.creator?.email === cal.id,
    );

    // Use calendar's background color if available, otherwise use default colors based on event type
    const eventColor =
      calendar?.backgroundColor || getDefaultEventColor(event.eventType);

    return eventColor;
  };

  // Default color scheme for events when no specific color is available
  const getDefaultEventColor = (eventType?: string) => {
    const colorMap: { [key: string]: string } = {
      birthday: "#f72585", // Pink
      outOfOffice: "#ff6d00", // Orange
      reminder: "#ffd60a", // Yellow
      appointment: "#003566", // Dark blue
      meeting: "#0077b6", // Blue
      task: "#00b4d8", // Light blue
      holiday: "#f72585", // Pink
      work: "#023e8a", // Navy
      travel: "#0077b6", // Blue
      sports: "#90e0ef", // Light cyan
      concert: "#7209b7", // Purple
      party: "#f72585", // Pink
      health: "#e63946", // Red
      study: "#f77f00", // Orange
      wedding: "#f72585", // Pink
      default: "#4285f4", // Google blue
    };

    return colorMap[eventType || "default"] || "#4285f4"; // Default blue
  };
  const dayEvents = useMemo(() => {
    // Constants for positioning
    const HOUR_HEIGHT = 64; // 64px per hour (h-16 in Tailwind)
    const START_HOUR = 0; // 12AM (midnight)
    const PIXELS_PER_MINUTE = HOUR_HEIGHT / 60;

    const selectedDateStr = selectedDate.toDateString();
    const dayEvents: EventPosition[] = [];

    events.forEach((event) => {
      const eventStart = new Date(
        event.start.dateTime || event.start.date || "",
      );
      const eventEnd = new Date(event.end.dateTime || event.end.date || "");

      // Check if event is on selected day
      if (
        eventStart.toDateString() === selectedDateStr &&
        event.start.dateTime &&
        event.end.dateTime
      ) {
        const startHour = eventStart.getHours();
        const startMinute = eventStart.getMinutes();
        const endHour = eventEnd.getHours();
        const endMinute = eventEnd.getMinutes();

        // Show events for all hours (0-23)
        if (startHour >= START_HOUR && startHour <= 23) {
          const top =
            ((startHour - START_HOUR) * 60 + startMinute) * PIXELS_PER_MINUTE;
          const height = Math.max(
            ((endHour - startHour) * 60 + (endMinute - startMinute)) *
              PIXELS_PER_MINUTE,
            50,
          );

          dayEvents.push({
            event,
            top,
            height,
            left: 0,
            width: 100,
          });
        }
      }
    });

    // Handle overlaps
    if (dayEvents.length > 1) {
      const sortedEvents = dayEvents.sort((a, b) => a.top - b.top);
      const overlapGroups: EventPosition[][] = [];

      sortedEvents.forEach((event) => {
        // Find all groups this event overlaps with
        const overlappingGroups = overlapGroups.filter((group) =>
          group.some(
            (existingEvent) =>
              event.top < existingEvent.top + existingEvent.height &&
              event.top + event.height > existingEvent.top,
          ),
        );

        if (overlappingGroups.length === 0) {
          overlapGroups.push([event]);
        } else if (overlappingGroups.length === 1) {
          overlappingGroups[0].push(event);
        } else {
          // Merge overlapping groups
          const mergedGroup = [event];
          overlappingGroups.forEach((group) => {
            mergedGroup.push(...group);
            const index = overlapGroups.indexOf(group);
            overlapGroups.splice(index, 1);
          });
          overlapGroups.push(mergedGroup);
        }
      });

      // Calculate positions for each group
      overlapGroups.forEach((group) => {
        const groupSize = group.length;
        const columnWidth = 100 / groupSize;

        group.forEach((event, index) => {
          event.left = index * columnWidth;
          event.width = columnWidth - 1; // Small gap between events
        });
      });
    }

    return dayEvents;
  }, [selectedDate, events]);

  // Navigation handlers
  const goToPreviousDay = () => {
    const newSelectedDate = new Date(selectedDate);
    newSelectedDate.setDate(selectedDate.getDate() - 1);
    setSelectedDate(newSelectedDate);

    // Update current week if we've moved to a different week
    const weekOfNewDate = new Date(newSelectedDate);
    setCurrentWeek(weekOfNewDate);
  };

  const goToNextDay = () => {
    const newSelectedDate = new Date(selectedDate);
    newSelectedDate.setDate(selectedDate.getDate() + 1);
    setSelectedDate(newSelectedDate);

    // Update current week if we've moved to a different week
    const weekOfNewDate = new Date(newSelectedDate);
    setCurrentWeek(weekOfNewDate);
  };

  const goToToday = () => {
    const today = new Date();
    setCurrentWeek(today);
    setSelectedDate(today);
  };

  // Get current month and year for header
  const monthYear = currentWeek.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  // Scroll to 8AM on mount (show morning schedule)
  useEffect(() => {
    if (scrollContainerRef.current) {
      // Scroll to 8AM (8 hours after midnight)
      const scrollToHour = 8;
      const scrollPosition = scrollToHour * 64; // 64px per hour (h-16)
      scrollContainerRef.current.scrollTop = scrollPosition;
    }
  }, []);

  // Auto-scroll date strip to center the selected date
  useEffect(() => {
    if (dateStripRef.current) {
      const selectedIndex = extendedDates.findIndex(
        (date) => date.toDateString() === selectedDate.toDateString(),
      );

      if (selectedIndex !== -1) {
        const container = dateStripRef.current;
        const buttons = container.querySelectorAll("button");

        if (buttons[selectedIndex]) {
          const selectedButton = buttons[selectedIndex];
          const containerRect = container.getBoundingClientRect();
          const buttonRect = selectedButton.getBoundingClientRect();

          // Calculate the position to center the button
          const scrollLeft = container.scrollLeft;
          const buttonCenter =
            buttonRect.left -
            containerRect.left +
            scrollLeft +
            buttonRect.width / 2;
          const containerCenter = containerRect.width / 2;
          const targetScrollLeft = buttonCenter - containerCenter;

          container.scrollTo({
            left: Math.max(0, targetScrollLeft),
            behavior: "smooth",
          });
        }
      }
    }
  }, [selectedDate, extendedDates]);

  return (
    <div className="flex h-full w-full justify-center p-4 pt-0">
      <div className="flex h-full w-full max-w-2xl flex-col">
        {/* Header Row */}
        <div className="flex items-center justify-between p-6 py-4">
          <h1 className="text-2xl font-semibold text-white">Calendar</h1>
          <div className="text-lg font-medium text-zinc-300">{monthYear}</div>
          <div className="flex items-center gap-3">
            <button
              onClick={goToPreviousDay}
              className="rounded-lg p-2 transition-colors hover:bg-zinc-800"
            >
              <ChevronLeft className="h-5 w-5 text-zinc-400" />
            </button>
            <button
              onClick={goToToday}
              className="rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-700"
            >
              Today
            </button>
            <button
              onClick={goToNextDay}
              className="rounded-lg p-2 transition-colors hover:bg-zinc-800"
            >
              <ChevronRight className="h-5 w-5 text-zinc-400" />
            </button>
          </div>
        </div>

        {/* Week Strip (Day Selector) */}
        <div className="border-b border-zinc-800 pb-2">
          <div
            ref={dateStripRef}
            className="flex gap-2 overflow-x-auto px-4"
            style={{
              scrollbarWidth: "none",
              msOverflowStyle: "none",
            }}
          >
            {extendedDates.map((date, index) => {
              const isSelected =
                date.toDateString() === selectedDate.toDateString();
              const isToday = date.toDateString() === new Date().toDateString();
              const isWeekend = date.getDay() === 0 || date.getDay() === 6; // Sunday or Saturday
              const isFirstDayOfWeek = date.getDay() === 0; // Sunday
              const dayLabel = date
                .toLocaleDateString("en-US", { weekday: "short" })
                .toUpperCase();
              const dayNumber = date.getDate();

              return (
                <div key={index} className="flex items-center">
                  {/* Week separator line - show before each Sunday (except the first one) */}
                  {isFirstDayOfWeek && index > 0 && (
                    <div className="w-px h-12 bg-zinc-700 mr-2 flex-shrink-0" />
                  )}
                  
                  <button
                    onClick={() => setSelectedDate(date)}
                    className={`flex min-w-[60px] flex-col items-center rounded-2xl px-3 py-2 transition-all duration-200 ${
                      isSelected
                        ? "bg-primary text-white"
                        : isToday
                          ? "bg-zinc-700 text-white"
                          : isWeekend
                            ? "bg-zinc-900 text-zinc-500 hover:bg-zinc-800"
                            : "text-zinc-400 hover:bg-zinc-800"
                    }`}
                  >
                    <div className="mb-1 text-xs font-medium">{dayLabel}</div>
                    <div
                      className={`text-lg font-semibold ${
                        isSelected
                          ? "text-white"
                          : isToday
                            ? "text-white"
                            : isWeekend
                              ? "text-zinc-400"
                              : "text-zinc-300"
                      }`}
                    >
                      {dayNumber}
                    </div>
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Single Day Calendar Grid */}
        <div className="flex-1 overflow-y-auto" ref={scrollContainerRef}>
          <div className="relative flex">
            {/* Time Labels Column */}
            <div className="w-20 flex-shrink-0 border-r border-zinc-800">
              {hours.map((hour) => (
                <div
                  key={hour}
                  className="flex h-16 items-start justify-end pt-2 pr-3"
                >
                  <span className="text-xs font-medium text-zinc-500">
                    {hour === 0
                      ? "12AM"
                      : hour === 12
                        ? "12PM"
                        : hour > 12
                          ? `${hour - 12}PM`
                          : `${hour}AM`}
                  </span>
                </div>
              ))}
            </div>

            {/* Main Calendar Column */}
            <div className="relative flex-1">
              {/* Hour Dividers */}
              {hours.map((hour) => (
                <div
                  key={`divider-${hour}`}
                  className="h-16 border-t border-zinc-800 first:border-t-0"
                />
              ))}

              {/* Events Container */}
              <div className="absolute inset-0 px-2">
                {loading.calendars ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="text-zinc-500">Loading calendars...</div>
                  </div>
                ) : error.calendars ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="text-center text-red-500">
                      <div className="text-lg font-medium">
                        Error loading calendars
                      </div>
                      <div className="mt-1 text-sm">{error.calendars}</div>
                    </div>
                  </div>
                ) : selectedCalendars.length === 0 ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="text-center text-zinc-500">
                      <div className="text-lg font-medium">
                        No calendars selected
                      </div>
                      <div className="mt-1 text-sm">
                        Please select a calendar to view events
                      </div>
                    </div>
                  </div>
                ) : loading.events ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="text-zinc-500">Loading events...</div>
                  </div>
                ) : error.events ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="text-center text-red-500">
                      <div className="text-lg font-medium">
                        Error loading events
                      </div>
                      <div className="mt-1 text-sm">{error.events}</div>
                    </div>
                  </div>
                ) : dayEvents.length === 0 ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="text-center text-zinc-500">
                      <div className="text-lg font-medium">
                        No events scheduled
                      </div>
                      <div className="mt-1 text-sm">
                        for{" "}
                        {selectedDate.toLocaleDateString("en-US", {
                          weekday: "long",
                          month: "long",
                          day: "numeric",
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  dayEvents.map((eventPos, eventIndex) => {
                    const eventColor = getEventColor(eventPos.event);
                    return (
                      <div
                        key={`event-${eventIndex}`}
                        className="absolute cursor-pointer rounded-lg border text-white shadow-lg transition-all duration-200 hover:opacity-80"
                        style={{
                          top: `${eventPos.top}px`,
                          height: `${eventPos.height}px`,
                          left: `${eventPos.left}%`,
                          width: `${eventPos.width - 1}%`,
                          backgroundColor: eventColor,
                          borderColor: eventColor,
                        }}
                        onClick={() => onEventClick?.(eventPos.event)}
                      >
                        <div className="p-3">
                          <div className="line-clamp-2 text-sm leading-tight font-medium">
                            {eventPos.event.summary}
                          </div>
                          {eventPos.event.start.dateTime &&
                            eventPos.event.end.dateTime && (
                              <div className="mt-1 text-xs text-white/80">
                                {new Date(
                                  eventPos.event.start.dateTime,
                                ).toLocaleTimeString("en-US", {
                                  hour: "numeric",
                                  minute: "2-digit",
                                  hour12: true,
                                })}{" "}
                                –{" "}
                                {new Date(
                                  eventPos.event.end.dateTime,
                                ).toLocaleTimeString("en-US", {
                                  hour: "numeric",
                                  minute: "2-digit",
                                  hour12: true,
                                })}
                              </div>
                            )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeeklyCalendarView;
