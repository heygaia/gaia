import { Chip } from "@heroui/chip";
import { Input } from "@heroui/input";
import { Textarea } from "@heroui/input";
import { Select, SelectItem } from "@heroui/select";
import { Tab,Tabs } from "@heroui/tabs";
import { Clock, Zap } from "lucide-react";
import { useState } from "react";

import {
  buildCronExpression,
  CronSchedule,
  getScheduleDescription,
  schedulePresets,
} from "../utils/cronUtils";

interface ScheduleBuilderProps {
  value?: string; // cron expression
  onChange: (cronExpression: string) => void;
}

export const ScheduleBuilder = ({
  value = "",
  onChange,
}: ScheduleBuilderProps) => {
  const [activeTab, setActiveTab] = useState<"presets" | "custom">("presets");
  const [selectedPreset, setSelectedPreset] = useState<string>("");
  const [customSchedule, setCustomSchedule] = useState<CronSchedule>({
    type: "daily",
    hour: 9,
    minute: 0,
  });
  const [customCron, setCustomCron] = useState("");

  const handlePresetSelect = (presetId: string) => {
    const preset = schedulePresets.find((p) => p.id === presetId);
    if (preset) {
      setSelectedPreset(presetId);
      onChange(preset.cron);
    }
  };

  const handleCustomScheduleChange = (updates: Partial<CronSchedule>) => {
    const newSchedule = { ...customSchedule, ...updates };
    setCustomSchedule(newSchedule);
    const cronExpr = buildCronExpression(newSchedule);
    onChange(cronExpr);
  };

  const handleCustomCronChange = (cron: string) => {
    setCustomCron(cron);
    onChange(cron);
  };

  const formatTime = (hour: number, minute: number) => {
    return `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
  };

  const renderPresets = () => (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-2">
        {schedulePresets.map((preset) => (
          <div
            key={preset.id}
            className={`cursor-pointer rounded-lg border p-3 transition-all ${
              selectedPreset === preset.id
                ? "border-primary bg-primary/10"
                : "border-zinc-700 hover:border-zinc-600"
            }`}
            onClick={() => handlePresetSelect(preset.id)}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-foreground-400" />
                  <span className="text-sm font-medium">{preset.label}</span>
                </div>
                <p className="mt-1 text-xs text-foreground-400">
                  {preset.description}
                </p>
              </div>
              <Chip size="sm" variant="flat" className="text-xs">
                {preset.cron}
              </Chip>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderCustomBuilder = () => (
    <div className="space-y-4">
      <Select
        label="Schedule Type"
        selectedKeys={customSchedule.type ? [customSchedule.type] : []}
        onSelectionChange={(keys) => {
          const type = Array.from(keys)[0] as CronSchedule["type"];
          handleCustomScheduleChange({ type });
        }}
      >
        <SelectItem key="daily">Daily</SelectItem>
        <SelectItem key="weekly">Weekly</SelectItem>
        <SelectItem key="monthly">Monthly</SelectItem>
        <SelectItem key="yearly">Yearly</SelectItem>
        <SelectItem key="custom">Custom Expression</SelectItem>
      </Select>

      {customSchedule.type !== "custom" && (
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Hour (0-23)"
            type="number"
            min="0"
            max="23"
            value={customSchedule.hour?.toString() || "9"}
            onChange={(e) =>
              handleCustomScheduleChange({
                hour: parseInt(e.target.value) || 9,
              })
            }
          />
          <Input
            label="Minute (0-59)"
            type="number"
            min="0"
            max="59"
            value={customSchedule.minute?.toString() || "0"}
            onChange={(e) =>
              handleCustomScheduleChange({
                minute: parseInt(e.target.value) || 0,
              })
            }
          />
        </div>
      )}

      {customSchedule.type === "weekly" && (
        <Select
          label="Day of Week"
          selectedKeys={
            customSchedule.dayOfWeek
              ? [customSchedule.dayOfWeek.toString()]
              : []
          }
          onSelectionChange={(keys) => {
            const dayOfWeek = parseInt(Array.from(keys)[0] as string);
            handleCustomScheduleChange({ dayOfWeek });
          }}
        >
          <SelectItem key="0">Sunday</SelectItem>
          <SelectItem key="1">Monday</SelectItem>
          <SelectItem key="2">Tuesday</SelectItem>
          <SelectItem key="3">Wednesday</SelectItem>
          <SelectItem key="4">Thursday</SelectItem>
          <SelectItem key="5">Friday</SelectItem>
          <SelectItem key="6">Saturday</SelectItem>
        </Select>
      )}

      {customSchedule.type === "monthly" && (
        <Input
          label="Day of Month (1-31)"
          type="number"
          min="1"
          max="31"
          value={customSchedule.dayOfMonth?.toString() || "1"}
          onChange={(e) =>
            handleCustomScheduleChange({
              dayOfMonth: parseInt(e.target.value) || 1,
            })
          }
        />
      )}

      {customSchedule.type === "yearly" && (
        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Month"
            selectedKeys={
              customSchedule.month ? [customSchedule.month.toString()] : []
            }
            onSelectionChange={(keys) => {
              const month = parseInt(Array.from(keys)[0] as string);
              handleCustomScheduleChange({ month });
            }}
          >
            <SelectItem key="1">January</SelectItem>
            <SelectItem key="2">February</SelectItem>
            <SelectItem key="3">March</SelectItem>
            <SelectItem key="4">April</SelectItem>
            <SelectItem key="5">May</SelectItem>
            <SelectItem key="6">June</SelectItem>
            <SelectItem key="7">July</SelectItem>
            <SelectItem key="8">August</SelectItem>
            <SelectItem key="9">September</SelectItem>
            <SelectItem key="10">October</SelectItem>
            <SelectItem key="11">November</SelectItem>
            <SelectItem key="12">December</SelectItem>
          </Select>
          <Input
            label="Day"
            type="number"
            min="1"
            max="31"
            value={customSchedule.dayOfMonth?.toString() || "1"}
            onChange={(e) =>
              handleCustomScheduleChange({
                dayOfMonth: parseInt(e.target.value) || 1,
              })
            }
          />
        </div>
      )}

      {customSchedule.type === "custom" && (
        <Textarea
          label="Cron Expression"
          placeholder="0 9 * * *"
          description="Format: minute hour day-of-month month day-of-week"
          value={customCron}
          onChange={(e) => handleCustomCronChange(e.target.value)}
        />
      )}

      {/* Preview */}
      <div className="rounded-lg bg-zinc-800/50 p-3">
        <div className="mb-2 flex items-center gap-2">
          <Zap className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Preview</span>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-foreground-400">
            {getScheduleDescription(buildCronExpression(customSchedule))}
          </p>
          <p className="font-mono text-xs text-foreground-500">
            {buildCronExpression(customSchedule)}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="w-full">
      <Tabs
        selectedKey={activeTab}
        onSelectionChange={(key) => setActiveTab(key as "presets" | "custom")}
        className="w-full"
      >
        <Tab key="presets" title="Quick Presets">
          {renderPresets()}
        </Tab>
        <Tab key="custom" title="Custom Schedule">
          {renderCustomBuilder()}
        </Tab>
      </Tabs>
    </div>
  );
};
