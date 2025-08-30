import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

import UpcomingEventsView from "@/features/calendar/components/UpcomingEventsView";
import UnreadEmailsView from "@/features/mail/components/UnreadEmailsView";
import { apiService } from "@/lib/api";
import { GoogleCalendarEvent } from "@/types/features/calendarTypes";
import { EmailData } from "@/types/features/mailTypes";

interface UnreadEmailsResponse {
  messages: EmailData[];
  nextPageToken?: string;
}

interface CalendarEventsResponse {
  events: GoogleCalendarEvent[];
  nextPageToken?: string;
}

export const GridSection = () => {
  const router = useRouter();

  const [emailData, setEmailData] = useState<EmailData[]>([]);
  const [calendarEvents, setCalendarEvents] = useState<GoogleCalendarEvent[]>(
    [],
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errors, setErrors] = useState<{
    email?: Error | null;
    calendar?: string | null;
  }>({});

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setErrors({});

      try {
        // Parallel API calls using Promise.all
        const [emailResponse, calendarResponse] = await Promise.all([
          apiService
            .get<UnreadEmailsResponse>(
              `/gmail/search?is_read=false&max_results=10`,
              { errorMessage: "Failed to fetch unread emails", silent: true },
            )
            .catch((err) => ({ error: err.message || "Email fetch failed" })),

          apiService
            .get<CalendarEventsResponse>(`/calendar/events?max_results=10`, {
              errorMessage: "Failed to fetch calendar events",
              silent: true,
            })
            .catch((err) => ({
              error: err.message || "Calendar fetch failed",
            })),
        ]);

        // Handle email response
        if ("error" in emailResponse) {
          setErrors((prev) => ({
            ...prev,
            email: new Error(emailResponse.error),
          }));
        } else {
          setEmailData(emailResponse.messages || []);
        }

        // Handle calendar response
        if ("error" in calendarResponse) {
          setErrors((prev) => ({ ...prev, calendar: calendarResponse.error }));
        } else {
          setCalendarEvents(calendarResponse.events || []);
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
        setErrors({
          email: new Error("Failed to load data"),
          calendar: "Failed to load data",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

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
