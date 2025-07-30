import Spinner from "@/components/ui/shadcn/spinner";
import CalendarSelector from "@/features/calendar/components/CalendarSelector";
import { useSharedCalendar } from "@/features/calendar/hooks/useSharedCalendar";

export default function CalendarSidebar() {
  const {
    calendars,
    selectedCalendars,
    handleCalendarSelect,
    isInitialized,
    loading,
  } = useSharedCalendar();

  if (!isInitialized || loading.calendars) {
    return (
      <div className="flex h-40 w-full flex-1 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div>
      <div className="w-full px-2 pt-0 pb-1 text-xs font-medium text-foreground-400">
        Your Calendars
      </div>
      <CalendarSelector
        calendars={calendars}
        selectedCalendars={selectedCalendars}
        onCalendarSelect={handleCalendarSelect}
      />
    </div>
  );
}
