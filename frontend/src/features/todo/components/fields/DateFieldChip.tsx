"use client";

import { Input } from "@heroui/react";
import { format, isToday, isTomorrow, isYesterday } from "date-fns";
import { Calendar, X } from "lucide-react";

import BaseFieldChip from "./BaseFieldChip";

interface DateFieldChipProps {
  value?: string; // ISO date string
  onChange: (date?: string, timezone?: string) => void;
  className?: string;
  timezone?: string; // User's preferred timezone
}

export default function DateFieldChip({
  value,
  onChange,
  className,
  timezone,
}: DateFieldChipProps) {
  // Use user's preferred timezone or fallback to browser timezone
  // Handle empty string as "auto-detect"
  const userTimezone =
    timezone && timezone.trim() !== ""
      ? timezone
      : Intl.DateTimeFormat().resolvedOptions().timeZone;
  const formatDisplayDate = (dateString: string) => {
    const date = new Date(dateString);

    if (isToday(date)) return "Today";
    if (isTomorrow(date)) return "Tomorrow";
    if (isYesterday(date)) return "Yesterday";

    return format(date, "MMM d");
  };

  const displayValue = value ? formatDisplayDate(value) : undefined;

  const handleDateInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    if (inputValue) {
      const date = new Date(inputValue);
      onChange(date.toISOString(), userTimezone);
    } else {
      onChange(undefined, undefined);
    }
  };

  const handleQuickDate = (days: number) => {
    const date = new Date();
    date.setDate(date.getDate() + days);
    onChange(date.toISOString(), userTimezone);
  };

  return (
    <BaseFieldChip
      label="Due Date"
      value={displayValue}
      placeholder="Due date"
      icon={<Calendar size={14} />}
      variant={value ? "success" : "default"}
      className={className}
    >
      <div className="p-1">
        <div className="border-0 bg-zinc-900 p-3">
          <label
            htmlFor="due-date-input"
            className="mb-2 block text-sm text-zinc-300"
          >
            Select Date
          </label>
          <Input
            id="due-date-input"
            type="date"
            value={value ? value.split("T")[0] : ""}
            onChange={handleDateInputChange}
            size="sm"
            variant="flat"
            className="w-full"
            aria-label="Select due date"
          />
        </div>

        {/* Quick date options */}
        <div
          onClick={(e) => {
            e.stopPropagation();
            handleQuickDate(0);
          }}
          className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-zinc-300 transition-colors hover:bg-zinc-800"
        >
          <Calendar size={14} />
          Today
        </div>
        <div
          onClick={(e) => {
            e.stopPropagation();
            handleQuickDate(1);
          }}
          className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-zinc-300 transition-colors hover:bg-zinc-800"
        >
          <Calendar size={14} />
          Tomorrow
        </div>
        <div
          onClick={(e) => {
            e.stopPropagation();
            handleQuickDate(3);
          }}
          className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-zinc-300 transition-colors hover:bg-zinc-800"
        >
          <Calendar size={14} />
          In 3 days
        </div>
        <div
          onClick={(e) => {
            e.stopPropagation();
            handleQuickDate(7);
          }}
          className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-zinc-300 transition-colors hover:bg-zinc-800"
        >
          <Calendar size={14} />
          Next week
        </div>

        {/* Clear date option */}
        {value && (
          <>
            <div className="my-1 h-px bg-zinc-700" />
            <div
              onClick={(e) => {
                e.stopPropagation();
                onChange(undefined, undefined);
              }}
              className="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-red-400 transition-colors hover:bg-zinc-800"
            >
              <X size={14} />
              Clear date
            </div>
          </>
        )}
      </div>
    </BaseFieldChip>
  );
}
