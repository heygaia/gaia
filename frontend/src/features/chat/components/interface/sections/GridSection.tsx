import { useRouter } from "next/navigation";
import React, { useEffect } from "react";

import { useSharedCalendar } from "@/features/calendar/hooks/useSharedCalendar";
import UpcomingEventsView from "@/features/calendar/components/UpcomingEventsView";
import { useUnreadEmails } from "@/features/mail/hooks/useUnreadEmails";
import UnreadEmailsView from "@/features/mail/components/UnreadEmailsView";

export const GridSection = () => {
  const router = useRouter();

  // Fetch both email and calendar data simultaneously
  const {
    data: unreadEmails,
    isLoading: emailLoading,
    error: emailError,
  } = useUnreadEmails(10);
  const {
    events,
    loading: calendarLoading,
    error: calendarError,
    calendars,
    selectedCalendars,
    isInitialized,
    loadCalendars,
    loadEvents,
  } = useSharedCalendar();

  // Initialize calendars on mount
  useEffect(() => {
    if (!isInitialized && !calendarLoading.calendars) {
      loadCalendars();
    }
  }, [isInitialized, calendarLoading.calendars, loadCalendars]);

  // Fetch events when selected calendars change or when calendars are first loaded
  useEffect(() => {
    if (selectedCalendars.length > 0 && isInitialized) {
      loadEvents(null, selectedCalendars, true);
    }
  }, [selectedCalendars, isInitialized, loadEvents]);

  return (
    <div className="relative flex h-fit snap-start flex-col items-center justify-center p-4">
      <div className="min-h-scree mb-20 grid w-full max-w-7xl grid-cols-1 grid-rows-1 gap-4 space-y-14 sm:min-h-[40vh] sm:grid-cols-2 sm:space-y-0">
        <UnreadEmailsView
          emails={unreadEmails}
          isLoading={emailLoading}
          error={emailError}
        />
        <UpcomingEventsView
          events={events}
          isLoading={calendarLoading.events}
          error={calendarError.events}
          calendars={calendars}
          onEventClick={(_event) => {
            router.push("/calendar");
          }}
        />
      </div>
    </div>
  );
};
