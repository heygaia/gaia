"use client";

import { Chip } from "@heroui/chip";
import { Clock, Mail } from "lucide-react";
import Image from "next/image";

import { CursorMagicSelection03Icon } from "@/components";
import { useIntegrations } from "@/features/integrations/hooks/useIntegrations";

import { Workflow } from "../api/workflowApi";
import { getTriggerDisplay } from "../utils/triggerDisplay";
import BaseWorkflowCard from "./shared/BaseWorkflowCard";

interface WorkflowCardProps {
  workflow: Workflow;
  onClick?: () => void;
}

const getTriggerIcon = (triggerType: string, integrationIconUrl?: string) => {
  // Use integration icon if available (Gmail, Calendar, etc.)
  if (integrationIconUrl) {
    return (
      <Image
        src={integrationIconUrl}
        alt="Integration icon"
        width={15}
        height={15}
      />
    );
  }

  // Fallback to type-specific icons only for non-integration triggers
  switch (triggerType) {
    case "schedule":
      return <Clock width={15} />;
    case "manual":
      return <CursorMagicSelection03Icon width={15} />;
    default:
      // For email/calendar without integration icon, show generic icon
      return <Mail width={15} />;
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
  const { integrations } = useIntegrations();

  // Get trigger display info using integration data
  const triggerDisplay = getTriggerDisplay(workflow, integrations);

  const footerContent = (
    <div className="mt-auto flex w-full flex-wrap items-center justify-between gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <Chip
          size="sm"
          startContent={getTriggerIcon(
            workflow.trigger_config.type,
            triggerDisplay.icon || undefined,
          )}
          className="flex gap-1 px-2!"
        >
          {triggerDisplay.label
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
  );

  return (
    <BaseWorkflowCard
      title={workflow.title}
      description={workflow.description}
      steps={workflow.steps}
      onClick={onClick}
      showArrowIcon={true}
      footerContent={footerContent}
    />
  );
}
