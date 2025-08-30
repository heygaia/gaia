"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

import { CalendarGrid } from "@/features/calendar/components/CalendarGrid";
import { CalendarHeader } from "@/features/calendar/components/CalendarHeader";
import { DateStrip } from "@/features/calendar/components/DateStrip";
import { useSharedCalendar } from "@/features/calendar/hooks/useSharedCalendar";
import { getEventColor } from "@/features/calendar/utils/eventColors";
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
  const [fetchedChunks, setFetchedChunks] = useState<Set<string>>(new Set());
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Helper function to get chunk key for a date (YYYY-MM format for quarterly chunks)
  const getChunkKey = (date: Date): string => {
    const year = date.getFullYear();
    const quarter = Math.floor(date.getMonth() / 3);
    return `${year}-Q${quarter + 1}`;
  };

  // Helper function to get chunk start/end dates
  const getChunkDates = (chunkKey: string): { start: Date; end: Date } => {
    const [year, quarter] = chunkKey.split("-");
    const quarterNum = parseInt(quarter.replace("Q", "")) - 1;

    const start = new Date(parseInt(year), quarterNum * 3, 1);
    const end = new Date(parseInt(year), (quarterNum + 1) * 3, 0, 23, 59, 59);

    return { start, end };
  };

  // Get required chunks for the current extended date range
  const getRequiredChunks = (dates: Date[]): string[] => {
    const chunks = new Set<string>();
    dates.forEach((date) => {
      chunks.add(getChunkKey(date));
    });
    return Array.from(chunks);
  };

  const {
    events,
    loading,
    error,
    calendars,
    selectedCalendars,
    isInitialized,
    loadCalendars,
    loadEvents,
  } = useSharedCalendar();

  // Generate hours from 12AM to 11PM for a full day view (24 hours)
  const hours = useMemo(() => {
    return Array.from({ length: 24 }, (_, i) => i); // 12AM to 11PM (0-23)
  }, []);

  // Get extended date range for horizontal scrolling (show 2 weeks before and after)
  const extendedDates = useMemo(() => {
    const startOfWeek = new Date(currentWeek);
    const day = startOfWeek.getDay();
    // Adjust to start from Monday (day 1) instead of Sunday (day 0)
    const daysFromMonday = day === 0 ? 6 : day - 1;
    startOfWeek.setDate(startOfWeek.getDate() - daysFromMonday - 14); // Go 2 weeks before Monday

    return Array.from({ length: 35 }, (_, i) => {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      return date;
    });
  }, [currentWeek]);

  // Initialize calendars on mount
  useEffect(() => {
    if (!isInitialized && !loading.calendars) {
      loadCalendars();
    }
  }, [isInitialized, loading.calendars, loadCalendars]);

  // Fetch events when selected calendars change, when calendars are first loaded, or when new chunks are needed
  useEffect(() => {
    if (
      selectedCalendars.length > 0 &&
      isInitialized &&
      extendedDates.length > 0
    ) {
      const requiredChunks = getRequiredChunks(extendedDates);
      const missingChunks = requiredChunks.filter(
        (chunk) => !fetchedChunks.has(chunk),
      );

      if (missingChunks.length > 0) {
        // Fetch all missing chunks in parallel
        const fetchPromises = missingChunks.map(async (chunkKey) => {
          const { start, end } = getChunkDates(chunkKey);

          try {
            await loadEvents(
              null,
              selectedCalendars,
              false, // Always append for chunked fetching
              start,
              end,
            );

            // Mark chunk as fetched
            setFetchedChunks((prev) => new Set([...prev, chunkKey]));
          } catch (error) {
            console.error(`Failed to fetch chunk ${chunkKey}:`, error);
          }
        });

        // Execute all chunk fetches
        Promise.all(fetchPromises);
      }
    }
  }, [
    selectedCalendars,
    isInitialized,
    extendedDates,
    fetchedChunks,
    loadEvents,
  ]);

  // Reset fetched chunks when selected calendars change
  useEffect(() => {
    setFetchedChunks(new Set());
    // Clear existing events when calendars change
    if (selectedCalendars.length > 0) {
      loadEvents(null, selectedCalendars, true); // Reset events for new calendars
    }
  }, [selectedCalendars, loadEvents]);

  // Wrapper function to maintain compatibility with CalendarGrid
  const getEventColorForGrid = (event: GoogleCalendarEvent) => {
    return getEventColor(event, calendars);
  };

  // Filter events for the selected day only and calculate positions
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

  // Helper function to scroll to the first event of the day
  const scrollToFirstEvent = (events: EventPosition[]) => {
    if (scrollContainerRef.current && events.length > 0) {
      // Find the earliest event
      const firstEvent = events.reduce((earliest, current) =>
        current.top < earliest.top ? current : earliest,
      );

      // Scroll to show the first event with some padding above
      const scrollPosition = Math.max(0, firstEvent.top - 100); // 100px padding above the event

      scrollContainerRef.current.scrollTo({
        top: scrollPosition,
        behavior: "smooth",
      });
    }
  };

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

  // Auto-scroll to first event when date changes (left/right navigation)
  useEffect(() => {
    if (dayEvents.length > 0) {
      // Small delay to ensure the view has updated
      const timeoutId = setTimeout(() => {
        scrollToFirstEvent(dayEvents);
      }, 100);

      return () => clearTimeout(timeoutId);
    } else {
      // If no events, scroll to 8AM
      if (scrollContainerRef.current) {
        const scrollToHour = 8;
        const scrollPosition = scrollToHour * 64; // 64px per hour (h-16)
        scrollContainerRef.current.scrollTo({
          top: scrollPosition,
          behavior: "smooth",
        });
      }
    }
  }, [selectedDate, dayEvents]);

  // Handler for date changes from header
  const handleDateChange = (date: Date) => {
    setSelectedDate(date);
    setCurrentWeek(date);
  };

  return (
    <div className="flex h-full w-full justify-center p-4 pt-0">
      <div className="flex h-full w-full max-w-2xl flex-col">
        <CalendarHeader
          selectedDate={selectedDate}
          onDateChange={handleDateChange}
          onPreviousDay={goToPreviousDay}
          onNextDay={goToNextDay}
          onToday={goToToday}
        />

        <DateStrip
          dates={extendedDates}
          selectedDate={selectedDate}
          onDateSelect={setSelectedDate}
        />

        <CalendarGrid
          ref={scrollContainerRef}
          hours={hours}
          dayEvents={dayEvents}
          loading={loading}
          error={error}
          selectedCalendars={selectedCalendars}
          selectedDate={selectedDate}
          onEventClick={onEventClick}
          getEventColor={getEventColorForGrid}
        />
      </div>
    </div>
  );
};

export default WeeklyCalendarView;
