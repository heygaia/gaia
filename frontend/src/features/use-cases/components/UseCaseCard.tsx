"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { ArrowUpRight, Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { ToolsIcon } from "@/components";
import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import { useWorkflowCreation } from "@/features/workflows/hooks/useWorkflowCreation";
import { useAppendToInput } from "@/stores/composerStore";

// Map integration names to the categories used in getToolCategoryIcon
const integrationToCategory: Record<string, string> = {
  gmail: "mail",
  gcal: "calendar",
  calendar: "calendar",
  gdocs: "google_docs",
  "google-docs": "google_docs",
  google_docs: "google_docs",
  notion: "notion",
  linear: "productivity",
  web: "search",
  "web search": "search",
  search: "search",
  mail: "mail",
  email: "mail",
  productivity: "productivity",
  documents: "documents",
  development: "development",
  memory: "memory",
  creative: "creative",
  weather: "weather",
  goal_tracking: "goal_tracking",
  webpage: "webpage",
  support: "support",
  general: "general",
};

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

  const handleCreateWorkflow = async () => {
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
        // Use selectWorkflow with autoSend option - this handles both navigation and auto-send flag
        selectWorkflow(result.workflow, { autoSend: true });
      }
    } catch (error) {
      toast.error("Error creating workflow", { id: toastId });
      console.error("Workflow creation error:", error);
    } finally {
      setIsCreatingWorkflow(false);
    }
  };

  const handleInsertPrompt = () => {
    if (prompt) appendToInput(prompt);
  };
  return (
    <div className="group relative flex min-h-[280px] w-full flex-col rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-6 transition duration-300">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {(() => {
            const validIcons = integrations
              .slice(0, 3)
              .map((integration) => {
                const category =
                  integrationToCategory[integration] || integration;
                const IconComponent = getToolCategoryIcon(category, {
                  width: 25,
                  height: 25,
                });
                return IconComponent ? (
                  <div
                    key={integration}
                    className="flex items-center justify-center"
                  >
                    {IconComponent}
                  </div>
                ) : null;
              })
              .filter(Boolean);

            return validIcons.length > 0 ? (
              validIcons
            ) : (
              <div className="flex items-center justify-center">
                <ToolsIcon
                  width={25}
                  height={25}
                  className="text-foreground-400"
                />
              </div>
            );
          })()}
          {integrations.length > 3 && (
            <div className="flex h-[40px] w-[40px] items-center justify-center rounded-lg bg-zinc-700 text-xs text-foreground-500">
              +{integrations.length - 3}
            </div>
          )}
        </div>

        <Chip
          size="sm"
          radius="sm"
          variant="flat"
          color={action_type === "workflow" ? "warning" : "secondary"}
          className="text-xs"
        >
          {action_type === "workflow" ? "Workflow" : "Use Case"}
        </Chip>
      </div>

      <h3 className="text-xl font-medium">{title}</h3>
      <div className="mb-4 line-clamp-3 flex-1 text-sm text-foreground-500">
        {description}
      </div>

      <div className="flex w-full flex-col gap-3">
        <Button
          color="default"
          size="sm"
          startContent={
            action_type === "prompt" ? (
              <ArrowUpRight width={16} height={16} />
            ) : (
              <Plus width={16} height={16} />
            )
          }
          className="w-full"
          isLoading={action_type === "workflow" && isCreatingWorkflow}
          onPress={
            action_type === "prompt" ? handleInsertPrompt : handleCreateWorkflow
          }
        >
          {action_type === "prompt" ? "Insert Prompt" : "Create Workflow"}
        </Button>
      </div>
    </div>
  );
}
