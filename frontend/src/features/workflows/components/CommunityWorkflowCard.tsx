"use client";

import { Button } from "@heroui/button";
import { ChevronUp, Plus, User } from "lucide-react";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import { useWorkflowCreation } from "@/features/workflows/hooks/useWorkflowCreation";

import { CommunityWorkflow, workflowApi } from "../api/workflowApi";

interface CommunityWorkflowCardProps {
  workflow: CommunityWorkflow;
}

export default function CommunityWorkflowCard({
  workflow,
}: CommunityWorkflowCardProps) {
  const [isCreatingWorkflow, setIsCreatingWorkflow] = useState(false);
  const [isUpvoting, setIsUpvoting] = useState(false);
  const [localWorkflow, setLocalWorkflow] = useState(workflow);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { selectWorkflow } = useWorkflowSelection();
  const { createWorkflow } = useWorkflowCreation();

  // Sync local state when workflow prop changes
  useEffect(() => {
    setLocalWorkflow(workflow);
  }, [workflow]);

  const handleCreateWorkflow = async () => {
    setIsCreatingWorkflow(true);
    const toastId = toast.loading("Creating workflow...");

    try {
      const workflowRequest = {
        title: localWorkflow.title,
        description: localWorkflow.description,
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
        selectWorkflow(result.workflow, { autoSend: false });
      }
    } catch (error) {
      toast.error("Error creating workflow", { id: toastId });
      console.error("Workflow creation error:", error);
    } finally {
      setIsCreatingWorkflow(false);
    }
  };

  const handleUpvoteImmediate = useCallback(async () => {
    if (isUpvoting) return;

    setIsUpvoting(true);

    // Store the current state for potential rollback
    const previousState = {
      is_upvoted: localWorkflow.is_upvoted,
      upvotes: localWorkflow.upvotes,
    };

    // Optimistic update - predict the action based on current state
    const predictedAction = localWorkflow.is_upvoted ? "removed" : "added";

    // Apply optimistic update immediately
    setLocalWorkflow((prev: CommunityWorkflow) => ({
      ...prev,
      is_upvoted: predictedAction === "added",
      upvotes:
        predictedAction === "added" ? prev.upvotes + 1 : prev.upvotes - 1,
    }));

    try {
      const result = await workflowApi.upvoteWorkflow(localWorkflow.id);

      // Verify optimistic update was correct, if not, apply correct state
      if (result.action !== predictedAction) {
        setLocalWorkflow((prev: CommunityWorkflow) => ({
          ...prev,
          is_upvoted: result.action === "added",
          upvotes:
            result.action === "added"
              ? previousState.upvotes + 1
              : previousState.upvotes - 1,
        }));
      }
    } catch (error) {
      console.error("Error upvoting workflow:", error);
      toast.error("Failed to update vote. Please try again.");

      // Rollback to previous state on error
      setLocalWorkflow((prev: CommunityWorkflow) => ({
        ...prev,
        is_upvoted: previousState.is_upvoted,
        upvotes: previousState.upvotes,
      }));
    } finally {
      setIsUpvoting(false);
    }
  }, [
    isUpvoting,
    localWorkflow.is_upvoted,
    localWorkflow.upvotes,
    localWorkflow.id,
  ]);

  const handleUpvote = useCallback(() => {
    // Prevent rapid clicks by checking if already processing
    if (isUpvoting) return;

    // Clear any existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Set new timeout for debouncing
    debounceTimeoutRef.current = setTimeout(() => {
      handleUpvoteImmediate();
    }, 300); // 300ms debounce
  }, [isUpvoting, handleUpvoteImmediate]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="group relative flex min-h-[300px] w-full flex-col rounded-2xl border-1 border-zinc-800 bg-zinc-800 p-6 transition duration-300">
      {/* Header with tool icons and creator info */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-center gap-2">
          {(() => {
            const categories = [
              ...new Set(
                localWorkflow.steps.map(
                  (step: { tool_category: string }) => step.tool_category,
                ),
              ),
            ];
            const validIcons = categories
              .slice(0, 3)
              .map((category) => {
                const IconComponent = getToolCategoryIcon(category as string, {
                  width: 25,
                  height: 25,
                });
                return IconComponent ? (
                  <div
                    key={category as string}
                    className="flex items-center justify-center"
                  >
                    {IconComponent}
                  </div>
                ) : null;
              })
              .filter(Boolean);

            return validIcons.length > 0 ? validIcons : null;
          })()}
          {[
            ...new Set(
              localWorkflow.steps.map(
                (step: { tool_category: string }) => step.tool_category,
              ),
            ),
          ].length > 3 && (
            <div className="flex h-[25px] w-[25px] items-center justify-center rounded-lg bg-zinc-700 text-xs text-foreground-500">
              +
              {[
                ...new Set(
                  localWorkflow.steps.map(
                    (step: { tool_category: string }) => step.tool_category,
                  ),
                ),
              ].length - 3}
            </div>
          )}
        </div>
      </div>

      <h3 className="text-xl font-medium">{localWorkflow.title}</h3>
      <div className="mb-4 line-clamp-3 flex-1 text-sm text-foreground-500">
        {localWorkflow.description}
      </div>

      {/* Creator info */}
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full">
          {localWorkflow.creator.avatar ? (
            <Image
              src={localWorkflow.creator.avatar}
              alt={localWorkflow.creator.name}
              width={27}
              height={27}
              className="rounded-full"
            />
          ) : (
            <User className="h-4 w-4 text-zinc-400" />
          )}
        </div>
        <div className="flex min-w-0 flex-1 flex-col">
          <p className="truncate text-xs font-medium text-zinc-400">
            {localWorkflow.creator.name}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex w-full items-center gap-3">
        <Button
          color="default"
          size="sm"
          startContent={<Plus width={16} height={16} />}
          className="flex-1"
          isLoading={isCreatingWorkflow}
          onPress={handleCreateWorkflow}
        >
          Create Workflow
        </Button>

        <Button
          variant={localWorkflow.is_upvoted ? "solid" : "flat"}
          color={localWorkflow.is_upvoted ? "primary" : "default"}
          size="sm"
          isIconOnly
          isLoading={isUpvoting}
          onPress={handleUpvote}
          className={`flex flex-shrink-0 flex-col`}
        >
          <ChevronUp width={50} height={50} />
          <span
            className={`min-w-0 text-xs font-bold ${localWorkflow.is_upvoted ? "text-black" : "text-zinc-500"}`}
          >
            {localWorkflow.upvotes}
          </span>
        </Button>
      </div>
    </div>
  );
}
