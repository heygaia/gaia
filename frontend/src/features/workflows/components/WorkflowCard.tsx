"use client";

import { Chip } from "@heroui/chip";
import { Tooltip } from "@heroui/tooltip";
import { ArrowUpRight, Clock, Mail, MousePointer } from "lucide-react";

import { CalendarIcon } from "@/components";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";

import { Workflow } from "../api/workflowApi";
import { getScheduleDescription } from "../utils/cronUtils";
import { WorkflowGeneratingShimmer } from "./WorkflowGeneratingShimmer";

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
      return <MousePointer width={15} />;
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

const getActivationColor = (activated: boolean) => {
  return activated ? "success" : "default";
};

const getActivationLabel = (activated: boolean) => {
  return activated ? "Activated" : "Deactivated";
};

export default function WorkflowCard({ workflow, onClick }: WorkflowCardProps) {
  return (
    <div
      className="group relative flex aspect-square cursor-pointer flex-col rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-4 transition duration-300 hover:scale-105 hover:border-zinc-600"
      onClick={onClick}
    >
      <ArrowUpRight
        className="absolute top-4 right-4 text-foreground-400 opacity-0 transition group-hover:opacity-100"
        width={25}
        height={25}
      />

      {/* Tool icons from workflow steps */}
      <div className="flex items-center gap-2">
        {workflow.steps.length > 0 && (
          <>
            {[...new Set(workflow.steps.map((step) => step.tool_category))]
              .slice(0, 3)
              .map((category, index) => (
                <div className="flex h-[40px] w-[40px] items-center justify-center rounded-lg">
                  {getToolCategoryIcon(category, {
                    size: 20,
                    width: 20,
                    height: 20,
                  })}
                </div>
              ))}

            {[...new Set(workflow.steps.map((step) => step.tool_category))]
              .length > 3 && (
              <div className="flex h-[40px] w-[40px] items-center justify-center rounded-lg bg-zinc-700">
                <span className="text-xs font-bold">
                  +
                  {[
                    ...new Set(
                      workflow.steps.map((step) => step.tool_category),
                    ),
                  ].length - 3}
                </span>
              </div>
            )}
          </>
        )}
      </div>

      <h3 className="mt-4 truncate font-medium">{workflow.title}</h3>
      <div className="line-clamp-2 flex-1 text-sm text-foreground-500">
        {workflow.description}
      </div>

      <div className="flex w-full items-center justify-between">
        <Chip
          size="sm"
          startContent={getTriggerIcon(workflow.trigger_config.type)}
          className="flex gap-1 px-2!"
        >
          {getTriggerLabel(workflow)}
        </Chip>

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
