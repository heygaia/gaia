import { Input } from "@heroui/input";
import { Textarea } from "@heroui/input";
import { Select, SelectItem } from "@heroui/select";
import { useState } from "react";

import { buildCronExpression, CronSchedule } from "../utils/cronUtils";

interface ScheduleBuilderProps {
  value?: string; // cron expression
  onChange: (cronExpression: string) => void;
}

export const ScheduleBuilder = ({ onChange }: ScheduleBuilderProps) => {
  const [simpleSchedule, setSimpleSchedule] = useState({
    frequency: "every", // "every" | "once" | "custom"
    interval: "day", // "day" | "week" | "month"
    dayOfWeek: "1", // for weekly
    dayOfMonth: "1", // for monthly
    hour: "9",
    minute: "0",
  });
  const [customCron, setCustomCron] = useState("");

  const handleSimpleScheduleChange = (
    updates: Partial<typeof simpleSchedule>,
  ) => {
    const newSchedule = { ...simpleSchedule, ...updates };
    setSimpleSchedule(newSchedule);

    // Only generate cron if not in custom mode
    if (newSchedule.frequency !== "custom") {
      // Convert to cron expression
      let cronSchedule: CronSchedule;
      switch (newSchedule.interval) {
        case "day":
          cronSchedule = {
            type: "daily",
            hour: parseInt(newSchedule.hour),
            minute: parseInt(newSchedule.minute),
          };
          break;
        case "week":
          cronSchedule = {
            type: "weekly",
            hour: parseInt(newSchedule.hour),
            minute: parseInt(newSchedule.minute),
            dayOfWeek: parseInt(newSchedule.dayOfWeek),
          };
          break;
        case "month":
          cronSchedule = {
            type: "monthly",
            hour: parseInt(newSchedule.hour),
            minute: parseInt(newSchedule.minute),
            dayOfMonth: parseInt(newSchedule.dayOfMonth),
          };
          break;
        default:
          cronSchedule = {
            type: "daily",
            hour: parseInt(newSchedule.hour),
            minute: parseInt(newSchedule.minute),
          };
      }

      const cronExpr = buildCronExpression(cronSchedule);
      onChange(cronExpr);
    }
  };

  const handleCustomCronChange = (cron: string) => {
    setCustomCron(cron);
    onChange(cron);
  };

  return (
    <div className="w-full">
      {/* Natural Language Schedule Builder */}
      <div className="flex w-full flex-row items-center gap-3 text-sm">
        <span>Run</span>

        <Select
          aria-label="Select every or once or custom"
          size="sm"
          selectedKeys={[simpleSchedule.frequency]}
          onSelectionChange={(keys) =>
            handleSimpleScheduleChange({
              frequency: Array.from(keys)[0] as string,
            })
          }
          className="min-w-26"
        >
          <SelectItem key="every">Every</SelectItem>
          <SelectItem key="once">Once</SelectItem>
          <SelectItem key="custom">Custom</SelectItem>
        </Select>

        {simpleSchedule.frequency !== "custom" && (
          <>
            <Select
              size="sm"
              aria-label="Select day or week or month"
              selectedKeys={[simpleSchedule.interval]}
              onSelectionChange={(keys) =>
                handleSimpleScheduleChange({
                  interval: Array.from(keys)[0] as string,
                })
              }
              className="min-w-26"
            >
              <SelectItem key="day">Day</SelectItem>
              <SelectItem key="week">Week</SelectItem>
              <SelectItem key="month">Month</SelectItem>
            </Select>

            {simpleSchedule.interval === "week" && (
              <>
                <span>on</span>
                <Select
                  size="sm"
                  selectedKeys={[simpleSchedule.dayOfWeek]}
                  onSelectionChange={(keys) =>
                    handleSimpleScheduleChange({
                      dayOfWeek: Array.from(keys)[0] as string,
                    })
                  }
                  className="min-w-32"
                >
                  <SelectItem key="1">Monday</SelectItem>
                  <SelectItem key="2">Tuesday</SelectItem>
                  <SelectItem key="3">Wednesday</SelectItem>
                  <SelectItem key="4">Thursday</SelectItem>
                  <SelectItem key="5">Friday</SelectItem>
                  <SelectItem key="6">Saturday</SelectItem>
                  <SelectItem key="0">Sunday</SelectItem>
                </Select>
              </>
            )}

            {simpleSchedule.interval === "month" && (
              <>
                <span className="text-nowrap">on the</span>
                <Select
                  aria-label="Select day of the month"
                  size="sm"
                  selectedKeys={[simpleSchedule.dayOfMonth]}
                  onSelectionChange={(keys) =>
                    handleSimpleScheduleChange({
                      dayOfMonth: Array.from(keys)[0] as string,
                    })
                  }
                  className="min-w-20"
                >
                  {Array.from({ length: 31 }, (_, i) => (
                    <SelectItem key={(i + 1).toString()}>{i + 1}</SelectItem>
                  ))}
                </Select>
              </>
            )}

            <span>at</span>
            <div className="flex items-center gap-1">
              <Input
                size="sm"
                type="number"
                min="0"
                max="23"
                value={simpleSchedule.hour}
                onChange={(e) =>
                  handleSimpleScheduleChange({ hour: e.target.value })
                }
                className="w-16"
              />
              <span>:</span>
              <Input
                size="sm"
                type="number"
                min="0"
                max="59"
                value={simpleSchedule.minute}
                onChange={(e) =>
                  handleSimpleScheduleChange({ minute: e.target.value })
                }
                className="w-16"
              />
            </div>
          </>
        )}
      </div>

      {simpleSchedule.frequency === "custom" && (
        <div className="mt-4 w-full">
          <Textarea
            placeholder="0 9 * * *"
            description="Format: minute hour day-of-month month day-of-week"
            value={customCron}
            label="Cron Job"
            fullWidth
            onChange={(e) => handleCustomCronChange(e.target.value)}
          />
        </div>
      )}
    </div>
  );
};
