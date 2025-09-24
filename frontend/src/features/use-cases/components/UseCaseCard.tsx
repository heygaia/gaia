"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { ArrowUpRight, Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";
import { useWorkflowCreation } from "@/features/workflows/hooks/useWorkflowCreation";
import BaseWorkflowCard from "@/features/workflows/components/shared/BaseWorkflowCard";
import { useAppendToInput } from "@/stores/composerStore";

interface UseCaseCardProps {
  title: string;
  description: string;
  action_type: "prompt" | "workflow";
  integrations: string[];
  prompt?: string;
}

export default function UseCaseCard({
  title,
  description,
  action_type,
  integrations,
  prompt,
}: UseCaseCardProps) {
  const [isCreatingWorkflow, setIsCreatingWorkflow] = useState(false);
  const appendToInput = useAppendToInput();
  const { selectWorkflow } = useWorkflowSelection();
  const { createWorkflow } = useWorkflowCreation();

  // Unified action handler for both card and button
  const handleAction = async () => {
    if (action_type === "prompt") {
      if (prompt) appendToInput(prompt);
    } else {
      setIsCreatingWorkflow(true);
      const toastId = toast.loading("Creating workflow...");
      try {
        const workflowRequest = {
          title,
          description,
          trigger_config: {
            type: "manual" as const,
            enabled: true,
          },
          generate_immediately: true,
        };
        const result = await createWorkflow(workflowRequest);
        if (result.success && result.workflow) {
          toast.success("Workflow created successfully!", { id: toastId });
          selectWorkflow(result.workflow, { autoSend: true });
        }
      } catch (error) {
        toast.error("Error creating workflow", { id: toastId });
        console.error("Workflow creation error:", error);
      } finally {
        setIsCreatingWorkflow(false);
      }
    }
  };

  const isLoading = action_type === "workflow" && isCreatingWorkflow;
  const footerContent = (
    <div className="flex w-full flex-col gap-3">
      <Button
        color="default"
        size="sm"
        startContent={
          !isLoading ? (
            action_type === "prompt" ? (
              <ArrowUpRight width={16} height={16} />
            ) : (
              <Plus width={16} height={16} />
            )
          ) : undefined
        }
        className="w-full"
        isLoading={isLoading}
        onPress={handleAction}
      >
        {action_type === "prompt" ? "Insert Prompt" : "Create Workflow"}
      </Button>
    </div>
  );

  // Only make the card clickable if there is a single action and no modal
  const isCardClickable = true;

  return (
    <BaseWorkflowCard
      title={title}
      description={description}
      integrations={integrations}
      footerContent={footerContent}
      onClick={isCardClickable ? handleAction : undefined}
      showArrowIcon={false}
    />
  );
}
