"use client";

import { useEffect, useRef, useState } from "react";

import { Calendar01Icon } from "@/components";
import Spinner from "@/components/ui/shadcn/spinner";
import CalendarCard from "@/features/calendar/components/CalendarCard";
import CalendarEventDialog from "@/features/calendar/components/CalendarEventDialog";
import { useEventGroups } from "@/features/calendar/hooks/useEventGroups";
import { useSharedCalendar } from "@/features/calendar/hooks/useSharedCalendar";
import { GoogleCalendarEvent } from "@/types/features/calendarTypes";

export default function Calendar() {
  const [selectedEvent, setSelectedEvent] =
    useState<GoogleCalendarEvent | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState<boolean>(false);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState<boolean>(false);
  const observerRef = useRef<HTMLDivElement | null>(null);

  const {
    calendars,
    selectedCalendars,
    events,
    nextPageToken,
    loading,
    error,
    isInitialized,
    loadCalendars,
    loadEvents,
    clearEvents,
  } = useSharedCalendar();

  const groupedEventsByMonth = useEventGroups(events);

  // Initialize calendars on mount
  useEffect(() => {
    if (!isInitialized && !loading.calendars) {
      loadCalendars();
    }
  }, [isInitialized, loading.calendars, loadCalendars]);

  // Fetch events when selected calendars change
  useEffect(() => {
    if (selectedCalendars.length > 0) {
      clearEvents();
      loadEvents(null, selectedCalendars, true);
    }
  }, [selectedCalendars, clearEvents, loadEvents]);

  // Infinite scroll for loading more events
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (
          entry.isIntersecting &&
          !loading.events &&
          nextPageToken &&
          selectedCalendars.length > 0
        ) {
          loadEvents(nextPageToken, selectedCalendars);
        }
      },
      { rootMargin: "0px" },
    );
    const currentElement = observerRef.current;
    if (currentElement) observer.observe(currentElement);

    return () => {
      if (currentElement) observer.unobserve(currentElement);
    };
  }, [loading.events, nextPageToken, loadEvents, selectedCalendars]);

  const handleEventClick = (event: GoogleCalendarEvent) => {
    setSelectedEvent(event);
    setIsDialogOpen(true);
  };

  return (
    <>
      <div className="relative flex h-full w-full flex-col overflow-y-auto">
        {(error.calendars || error.events) && (
          <div className="flex flex-col items-center gap-2 pb-6">
            {error.calendars && (
              <div className="mb-4 w-full max-w-md rounded-lg bg-red-500/20 p-3 text-center text-sm text-red-500">
                {error.calendars}
              </div>
            )}

            {error.events && (
              <div className="mb-4 w-full max-w-md rounded-lg bg-red-500/20 p-3 text-center text-sm text-red-500">
                {error.events}
              </div>
            )}
          </div>
        )}

        <div className="mx-auto w-full max-w-(--breakpoint-sm)">
          {groupedEventsByMonth && Object.keys(groupedEventsByMonth).length > 0
            ? Object.entries(groupedEventsByMonth).map(([month, days]) => (
                <div key={month}>
                  <div className="sticky top-0 z-10 rounded-xl bg-zinc-800 p-2">
                    <div className="text-md text-center font-medium">
                      {month}
                    </div>
                  </div>
                  {Object.entries(days).map(([day, events]) => (
                    <div key={day} className="my-2 flex gap-7">
                      <div className="flex max-h-[60px] min-h-[60px] max-w-[60px] min-w-[60px] flex-col items-center justify-center rounded-full bg-zinc-800 text-center text-lg leading-none font-bold text-foreground-500">
                        <div className="text-md font-normal">
                          {day.split(" ")[1]}
                        </div>
                        <div className="text-foreground-600">
                          {day.split(" ")[0]}
                        </div>
                      </div>
                      <div className="flex w-full flex-wrap justify-center gap-4">
                        {events.map((event) => (
                          <CalendarCard
                            key={event.id}
                            calendars={calendars}
                            event={event}
                            onClick={() => handleEventClick(event)}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ))
            : !loading.events &&
              selectedCalendars.length > 0 && (
                <div className="flex h-[60vh] flex-col items-center justify-center text-center">
                  <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-zinc-800/50">
                    <Calendar01Icon className="h-12 w-12 text-zinc-400" />
                  </div>
                  <h3 className="mb-2 text-xl font-semibold text-zinc-300">
                    No events scheduled
                  </h3>
                  <p className="max-w-md text-zinc-500">
                    You don't have any events in your selected calendars yet.
                    Events will appear here once you add them.
                  </p>
                </div>
              )}
        </div>

        {loading.events && (
          <div className="flex h-[80vh] items-center justify-center">
            <Spinner />
          </div>
        )}
        <div ref={observerRef} className="h-1" />
      </div>

      {selectedEvent && (
        <CalendarEventDialog
          event={selectedEvent}
          open={isDialogOpen}
          onOpenChange={setIsDialogOpen}
        />
      )}

      {isAddDialogOpen && (
        <CalendarEventDialog
          event={null}
          open={isAddDialogOpen}
          onOpenChange={setIsAddDialogOpen}
          mode="create"
        />
      )}
    </>
  );
}
