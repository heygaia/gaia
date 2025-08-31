import { useRouter } from "next/navigation";
import React from "react";

import UpcomingEventsView from "@/features/calendar/components/UpcomingEventsView";
import { useUpcomingEventsQuery } from "@/features/calendar/hooks/useUpcomingEventsQuery";
import UnreadEmailsView from "@/features/mail/components/UnreadEmailsView";
import { useUnreadEmailsQuery } from "@/features/mail/hooks/useUnreadEmailsQuery";

export const GridSection = () => {
  const router = useRouter();

  // React Query automatically executes these queries in parallel
  const emailQuery = useUnreadEmailsQuery(20);
  const calendarQuery = useUpcomingEventsQuery(20);

  // Extract data with fallbacks
  const emailData = emailQuery.data ?? [];
  const calendarEvents = calendarQuery.data ?? [];

  // Individual loading states for granular control
  const emailLoading = emailQuery.isLoading;
  const calendarLoading = calendarQuery.isLoading;

  // Combined loading state - true if ANY query is still loading
  const isLoading = emailLoading || calendarLoading;

  // Transform errors to match expected format
  const errors = {
    email: emailQuery.error
      ? new Error(emailQuery.error.message || "Failed to load emails")
      : null,
    calendar: calendarQuery.error
      ? calendarQuery.error.message || "Failed to load events"
      : null,
  };

  return (
    <div className="relative flex h-fit snap-start flex-col items-center justify-center p-4">
      <div className="min-h-scree mb-20 grid w-full max-w-7xl grid-cols-1 grid-rows-1 gap-4 space-y-14 sm:min-h-[40vh] sm:grid-cols-2 sm:space-y-0">
        <UnreadEmailsView
          emails={emailData}
          isLoading={isLoading}
          error={errors.email}
        />
        <UpcomingEventsView
          events={calendarEvents}
          isLoading={isLoading}
          error={errors.calendar}
          calendars={[]}
          onEventClick={(_event) => {
            router.push("/calendar");
          }}
        />
      </div>
    </div>
  );
};
