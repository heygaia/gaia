"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Clock, Mail, Zap } from "lucide-react";
import Image from "next/image";
import { useState } from "react";

import { CursorMagicSelection03Icon } from "@/components";
import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";
import { useIntegrations } from "@/features/integrations/hooks/useIntegrations";
import { Workflow } from "@/features/workflows/api/workflowApi";
import { getTriggerDisplay } from "../../utils/triggerDisplay";
import BaseWorkflowCard from "./BaseWorkflowCard";

interface UnifiedWorkflowCardProps {
  workflow: Workflow;
  onClick?: () => void;
  variant?: "management" | "execution";
  showArrowIcon?: boolean;
}

const getTriggerIcon = (triggerType: string, integrationIconUrl?: string) => {
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

  switch (triggerType) {
    case "schedule":
      return <Clock width={15} />;
    case "manual":
      return <CursorMagicSelection03Icon width={15} />;
    default:
      return <Mail width={15} />;
  }
};

const getNextRunDisplay = (workflow: Workflow) => {
  const { trigger_config } = workflow;

  if (trigger_config.type === "schedule" && trigger_config.next_run) {
    const nextRun = new Date(trigger_config.next_run);
    const now = new Date();

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

export default function UnifiedWorkflowCard({
  workflow,
  onClick,
  variant = "management",
  showArrowIcon = false,
}: UnifiedWorkflowCardProps) {
  const [isRunning, setIsRunning] = useState(false);
  const { selectWorkflow } = useWorkflowSelection();
  const { integrations } = useIntegrations();

  const triggerDisplay = getTriggerDisplay(workflow, integrations);

  const handleRunWorkflow = async () => {
    if (isRunning) return;
    setIsRunning(true);
    try {
      selectWorkflow(workflow, { autoSend: true });
    } catch (error) {
      console.error("Error running workflow:", error);
    } finally {
      setIsRunning(false);
    }
  };

  const renderTriggerInfo = () => (
    <div className="flex flex-wrap items-center gap-2">
      <Chip
        size="sm"
        startContent={getTriggerIcon(
          workflow.trigger_config.type,
          triggerDisplay.icon || undefined,
        )}
        radius="sm"
        variant="light"
        className="flex gap-1 px-2! text-zinc-400"
      >
        {triggerDisplay.label
          .split(" ")
          .map(
            (word: string) =>
              word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
          )
          .join(" ")}
      </Chip>

      {getNextRunDisplay(workflow) && (
        <Chip
          size="sm"
          variant="flat"
          radius="sm"
          className="text-xs text-foreground-500"
        >
          {getNextRunDisplay(workflow)}
        </Chip>
      )}
    </div>
  );

  const footerContent =
    variant === "execution" ? (
      <div className="flex w-full flex-col gap-3">
        {renderTriggerInfo()}
        <Button
          color="primary"
          size="sm"
          isLoading={isRunning}
          onPress={handleRunWorkflow}
          variant="flat"
          className="ml-auto w-fit text-primary"
          startContent={<Zap width={16} height={16} />}
        >
          Run Workflow
        </Button>
      </div>
    ) : (
      <div className="mt-auto flex w-full flex-wrap items-center justify-between gap-2">
        {renderTriggerInfo()}
        <Chip
          color={getActivationColor(workflow.activated)}
          variant="flat"
          size="sm"
          radius="sm"
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
      onClick={variant === "execution" ? handleRunWorkflow : onClick}
      showArrowIcon={showArrowIcon}
      footerContent={footerContent}
      totalExecutions={workflow.total_executions}
    />
  );
}
