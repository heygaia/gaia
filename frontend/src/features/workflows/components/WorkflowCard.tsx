"use client";

import { Chip } from "@heroui/chip";
import { ArrowUpRight, Clock, Mail } from "lucide-react";

import { CalendarIcon, CursorMagicSelection03Icon } from "@/components";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";

import { Workflow } from "../api/workflowApi";
import { getScheduleDescription } from "../utils/cronUtils";

interface WorkflowCardProps {
  workflow: Workflow;
  onClick?: () => void;
}

const getTriggerIcon = (triggerType: string) => {
  switch (triggerType) {
    case "email":
      return <Mail width={15} />;
    case "schedule":
      return <Clock width={15} />;
    case "calendar":
      return <CalendarIcon width={15} />;
    default:
      return <CursorMagicSelection03Icon width={15} />;
  }
};

const getTriggerLabel = (workflow: Workflow) => {
  const { trigger_config } = workflow;

  switch (trigger_config.type) {
    case "email":
      return "on new emails";
    case "schedule":
      if (trigger_config.cron_expression) {
        return getScheduleDescription(trigger_config.cron_expression);
      }
      return "scheduled";
    case "calendar":
      return "calendar events";
    case "manual":
    default:
      return "manual trigger";
  }
};

const getNextRunDisplay = (workflow: Workflow) => {
  const { trigger_config } = workflow;

  if (trigger_config.type === "schedule" && trigger_config.next_run) {
    const nextRun = new Date(trigger_config.next_run);
    const now = new Date();

    // Check if next run is in the future
    if (nextRun > now) {
      const diffMs = nextRun.getTime() - now.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);

      if (diffDays > 0) {
        return `Next run in ${diffDays}d`;
      } else if (diffHours > 0) {
        return `Next run in ${diffHours}h`;
      } else {
        return "Running soon";
      }
    }
  }

  return null;
};

const getActivationColor = (activated: boolean) => {
  return activated ? "success" : "danger";
};

const getActivationLabel = (activated: boolean) => {
  return activated ? "Activated" : "Deactivated";
};

export default function WorkflowCard({ workflow, onClick }: WorkflowCardProps) {
  return (
    <div
      className="group relative flex min-h-[280px] w-full cursor-pointer flex-col rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-6 transition duration-300 hover:scale-105 hover:border-zinc-600"
      onClick={onClick}
    >
      <ArrowUpRight
        className="absolute top-4 right-4 text-foreground-400 opacity-0 transition group-hover:opacity-100"
        width={25}
        height={25}
      />

      {/* Tool icons from workflow steps */}
      <div className="flex items-start gap-2">
        {(() => {
          const categories = [
            ...new Set(workflow.steps.map((step) => step.tool_category)),
          ];
          const validIcons = categories
            .slice(0, 3)
            .map((category) => {
              const IconComponent = getToolCategoryIcon(category, {
                width: 25,
                height: 25,
              });
              return IconComponent ? (
                <div
                  key={category}
                  className="mb-3 flex items-center justify-center"
                >
                  {IconComponent}
                </div>
              ) : null;
            })
            .filter(Boolean);

          return validIcons.length > 0 ? validIcons : null;
        })()}
        {[...new Set(workflow.steps.map((step) => step.tool_category))].length >
          3 && (
          <div className="relative bottom-1 flex h-[30px] w-[30px] items-center justify-center rounded-lg bg-zinc-700 text-xs text-foreground-500">
            +
            {[...new Set(workflow.steps.map((step) => step.tool_category))]
              .length - 3}
          </div>
        )}
      </div>

      <h3 className="text-xl font-medium">{workflow.title}</h3>
      <div className="mb-4 line-clamp-3 flex-1 text-sm text-foreground-500">
        {workflow.description}
      </div>

      <div className="mt-auto flex w-full flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Chip
            size="sm"
            startContent={getTriggerIcon(workflow.trigger_config.type)}
            className="flex gap-1 px-2!"
          >
            {getTriggerLabel(workflow)
              .split(" ")
              .map(
                (word) =>
                  word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
              )
              .join(" ")}
          </Chip>

          {getNextRunDisplay(workflow) && (
            <Chip
              size="sm"
              variant="flat"
              className="text-xs text-foreground-500"
            >
              {getNextRunDisplay(workflow)}
            </Chip>
          )}
        </div>

        <Chip
          color={getActivationColor(workflow.activated)}
          variant="flat"
          size="sm"
        >
          {getActivationLabel(workflow.activated)}
        </Chip>
      </div>
    </div>
  );
}
