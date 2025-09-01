"use client";

import { Button } from "@heroui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@heroui/popover";
import { Select, SelectItem } from "@heroui/select";
import { ChevronLeft, ChevronRight } from "lucide-react";
import React, { useState } from "react";

interface CalendarHeaderProps {
  selectedDate: Date;
  onDateChange: (date: Date) => void;
  onPreviousDay: () => void;
  onNextDay: () => void;
  onToday: () => void;
}

export const CalendarHeader: React.FC<CalendarHeaderProps> = ({
  selectedDate,
  onDateChange,
  onPreviousDay,
  onNextDay,
  onToday,
}) => {
  const [showMonthYearPicker, setShowMonthYearPicker] = useState(false);

  // Get current month and year for header
  const monthYear = selectedDate.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  // Month/Year picker handlers
  const handleMonthYearChange = (month: number, year: number) => {
    const newDate = new Date(year, month, 1);
    onDateChange(newDate);
    setShowMonthYearPicker(false);
  };

  return (
    <div className="flex items-center justify-between p-6 py-4">
      <h1 className="text-2xl font-semibold text-white">Calendar</h1>

      <div className="relative">
        <Popover
          isOpen={showMonthYearPicker}
          onOpenChange={setShowMonthYearPicker}
        >
          <PopoverTrigger>
            <Button
              variant="flat"
              className="bg-zinc-800 text-lg font-medium text-zinc-300 hover:bg-zinc-700"
            >
              {monthYear}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="min-w-[280px] p-0">
            <div className="p-4">
              <h3 className="mb-3 text-sm font-medium text-zinc-300">
                Select Month & Year
              </h3>

              {/* Year selector */}
              <div className="mb-3">
                <Select
                  label="Year"
                  selectedKeys={[selectedDate.getFullYear().toString()]}
                  onSelectionChange={(keys) => {
                    const year = parseInt(Array.from(keys)[0] as string);
                    handleMonthYearChange(selectedDate.getMonth(), year);
                  }}
                  className="mb-3"
                  classNames={{
                    trigger: "bg-zinc-900 border-zinc-600",
                    value: "text-zinc-300",
                    label: "text-zinc-400",
                  }}
                >
                  {Array.from({ length: 11 }, (_, i) => {
                    const year = new Date().getFullYear() - 5 + i;
                    return (
                      <SelectItem key={year.toString()}>
                        {year.toString()}
                      </SelectItem>
                    );
                  })}
                </Select>
              </div>

              {/* Month grid */}
              <div>
                <label className="mb-2 block text-xs text-zinc-400">
                  Month
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {Array.from({ length: 12 }, (_, i) => {
                    const monthName = new Date(2025, i, 1).toLocaleDateString(
                      "en-US",
                      { month: "short" },
                    );
                    const isCurrentMonth = i === selectedDate.getMonth();
                    return (
                      <Button
                        key={i}
                        size="sm"
                        variant={isCurrentMonth ? "solid" : "flat"}
                        color={isCurrentMonth ? "primary" : "default"}
                        className={`${
                          isCurrentMonth
                            ? ""
                            : "bg-zinc-900 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-300"
                        }`}
                        onPress={() =>
                          handleMonthYearChange(i, selectedDate.getFullYear())
                        }
                      >
                        {monthName}
                      </Button>
                    );
                  })}
                </div>
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </div>

      <div className="flex items-center gap-3">
        <Button
          isIconOnly
          variant="flat"
          className="bg-transparent hover:bg-zinc-800"
          onPress={onPreviousDay}
        >
          <ChevronLeft className="h-5 w-5 text-zinc-400" />
        </Button>
        <Button
          variant="flat"
          className="bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
          onPress={onToday}
        >
          Today
        </Button>
        <Button
          isIconOnly
          variant="flat"
          className="bg-transparent hover:bg-zinc-800"
          onPress={onNextDay}
        >
          <ChevronRight className="h-5 w-5 text-zinc-400" />
        </Button>
      </div>
    </div>
  );
};
