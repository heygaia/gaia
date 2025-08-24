"use client";

import { useState } from "react";

import CalendarEventDialog from "@/features/calendar/components/CalendarEventDialog";
import WeeklyCalendarView from "@/features/calendar/components/WeeklyCalendarView";
import { GoogleCalendarEvent } from "@/types/features/calendarTypes";

export default function Calendar() {
  const [selectedEvent, setSelectedEvent] =
    useState<GoogleCalendarEvent | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState<boolean>(false);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState<boolean>(false);

  const handleEventClick = (event: GoogleCalendarEvent) => {
    setSelectedEvent(event);
    setIsDialogOpen(true);
  };

  return (
    <>
      <div className="relative flex h-full w-full">
        <WeeklyCalendarView onEventClick={handleEventClick} />
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
