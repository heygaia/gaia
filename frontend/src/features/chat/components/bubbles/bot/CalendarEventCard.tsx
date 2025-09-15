import { Button } from "@heroui/button";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { CalendarAdd01Icon, Tick02Icon } from "@/components/shared/icons";
import { calendarApi } from "@/features/calendar/api/calendarApi";
import { MotionContainer } from "@/layouts/MotionContainer";
import {
  CalendarEvent,
  EventCardProps,
  TimedEvent,
  UnifiedCalendarEventsListProps,
} from "@/types/features/calendarTypes";
import {
  formatAllDayDate,
  formatAllDayDateRange,
  formatTimedEventDate,
  getEventDurationText,
  isDateOnly,
} from "@/utils/date/calendarDateUtils";

const isTimedEvent = (event: CalendarEvent): event is TimedEvent =>
  "start" in event && "end" in event;

export function CalendarEventCard({
  event,
  isDummy,
  onDummyAddEvent,
}: EventCardProps) {
  const [status, setStatus] = useState<"idle" | "loading" | "added">("idle");

  const handleAddEvent = useCallback(async () => {
    if (isDummy) {
      setStatus("loading");
      setTimeout(() => {
        toast.success(`Event '${event.summary}' added!`, {
          description: event.description,
        });
        setStatus("added");
        onDummyAddEvent?.();
      }, 300);
      return;
    }

    setStatus("loading");
    try {
      const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

      // Handle different event types properly
      if (isTimedEvent(event)) {
        // Timed event with start and end times
        await calendarApi.createEventDefault({
          ...event,
          timezone: userTimeZone,
          is_all_day: event.is_all_day || false,
        });
      } else {
        // Single time event or all-day event
        await calendarApi.createEventDefault({
          summary: event.summary,
          description: event.description,
          is_all_day: true, // Assume single time events are all-day
          timezone: userTimeZone,
        });
      }
      setStatus("added");
    } catch (error) {
      console.error(error);
      setStatus("idle");
    }
  }, [event, isDummy, onDummyAddEvent]);

  return (
    <div className="mt-1 flex flex-col gap-2 rounded-xl bg-zinc-900 p-2">
      <div className="relative flex w-full flex-row gap-3 rounded-xl rounded-l-none bg-primary/20 p-3 pt-1 pr-1">
        <div className="absolute inset-0 w-1 rounded-full bg-primary" />
        <div className="flex flex-1 flex-col pl-1">
          <div className="flex w-full items-center justify-between">
            <div className="font-medium">{event.summary}</div>
          </div>
          <div className="text-xs text-primary">
            {isTimedEvent(event) ? (
              event.is_all_day ? (
                // All-day event display
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="rounded-md bg-primary/20 px-2 py-1 text-xs font-medium text-primary">
                      All Day
                    </span>
                  </div>
                  <div className="font-medium">
                    {event.start && event.end
                      ? isDateOnly(event.start) && isDateOnly(event.end)
                        ? formatAllDayDateRange(event.start, event.end)
                        : formatAllDayDateRange(
                            event.start.split("T")[0],
                            event.end.split("T")[0],
                          )
                      : event.start
                        ? formatAllDayDate(
                            isDateOnly(event.start)
                              ? event.start
                              : event.start.split("T")[0],
                          )
                        : "Date TBD"}
                  </div>
                  {event.start && event.end && (
                    <div className="text-xs opacity-70">
                      Duration: {getEventDurationText(event.start, event.end)}
                    </div>
                  )}
                </div>
              ) : (
                // Timed event display
                <div className="space-y-1">
                  <div className="flex items-center">
                    <span className="w-9 min-w-9 font-medium">Start:</span>
                    <span className="ml-1">
                      {formatTimedEventDate(event.start)}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span className="w-9 min-w-9 font-medium">End:</span>
                    <span className="ml-1">
                      {formatTimedEventDate(event.end)}
                    </span>
                  </div>
                  <div className="text-xs opacity-70">
                    Duration: {getEventDurationText(event.start, event.end)}
                  </div>
                </div>
              )
            ) : (
              // Single time event (fallback)
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  {/* <span className="rounded-md bg-primary/20 px-2 py-1 text-xs font-medium text-primary">
                    All Day
                  </span> */}
                </div>
                <div className="font-medium">{event.time || "Time TBD"}</div>
              </div>
            )}
          </div>
        </div>
      </div>
      <Button
        className="w-full"
        variant="flat"
        isDisabled={status === "added"}
        isLoading={status === "loading"}
        onPress={handleAddEvent}
      >
        {status === "added" ? (
          <Tick02Icon width={22} />
        ) : (
          <CalendarAdd01Icon width={22} />
        )}
        {status === "added" ? "Added" : "Add to calendar"}
      </Button>
    </div>
  );
}

export function CalendarEventsList({
  events,
  isDummy = false,
  onDummyAddEvent,
  disableAnimation = false,
}: UnifiedCalendarEventsListProps) {
  return (
    <MotionContainer
      disableAnimation={disableAnimation}
      className={`flex w-fit flex-col gap-1 rounded-2xl rounded-bl-none bg-zinc-800 p-4 pt-3 ${
        disableAnimation ? "mt-3" : ""
      }`}
    >
      <div>
        Would you like to add{" "}
        {events.length === 1 ? "this event" : "these events"} to your Calendar?
      </div>{" "}
      {events.map((event, index) => (
        <CalendarEventCard
          key={index}
          event={event}
          isDummy={isDummy}
          onDummyAddEvent={() => onDummyAddEvent?.(index)}
        />
      ))}
    </MotionContainer>
  );
}
