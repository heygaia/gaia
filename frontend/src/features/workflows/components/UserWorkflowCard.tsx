"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Play } from "lucide-react";
import { useState } from "react";

import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import { Workflow } from "@/features/workflows/api/workflowApi";

interface UserWorkflowCardProps {
  workflow: Workflow;
}

export default function UserWorkflowCard({ workflow }: UserWorkflowCardProps) {
  const [isRunning, setIsRunning] = useState(false);
  const { selectWorkflow } = useWorkflowSelection();

  const handleRunWorkflow = async () => {
    setIsRunning(true);

    try {
      // Select workflow with autoSend to automatically run it
      selectWorkflow(workflow, { autoSend: true });
    } catch (error) {
      console.error("Error running workflow:", error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="group relative flex min-h-[280px] w-full flex-col rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-6 transition duration-300">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
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
                    className="flex items-center justify-center"
                  >
                    {IconComponent}
                  </div>
                ) : null;
              })
              .filter(Boolean);

            return validIcons.length > 0 ? validIcons : null;
          })()}
          {[...new Set(workflow.steps.map((step) => step.tool_category))]
            .length > 3 && (
            <div className="flex h-[25px] w-[25px] items-center justify-center rounded-lg bg-zinc-700 text-xs text-foreground-500">
              +
              {[...new Set(workflow.steps.map((step) => step.tool_category))]
                .length - 3}
            </div>
          )}
        </div>

        <Chip
          size="sm"
          radius="sm"
          variant="flat"
          color="warning"
          className="text-xs"
        >
          Workflow
        </Chip>
      </div>

      <h3 className="text-xl font-medium">{workflow.title}</h3>
      <div className="mb-4 line-clamp-3 flex-1 text-sm text-foreground-500">
        {workflow.description}
      </div>

      <div className="flex w-full flex-col gap-3">
        <Button
          color="primary"
          size="sm"
          startContent={<Play width={16} height={16} />}
          className="w-full"
          isLoading={isRunning}
          onPress={handleRunWorkflow}
        >
          Run Workflow
        </Button>
      </div>
    </div>
  );
}
