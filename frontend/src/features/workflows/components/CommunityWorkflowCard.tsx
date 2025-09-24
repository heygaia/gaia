"use client";

import { Button } from "@heroui/button";
import { ChevronUp, Plus } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";
import { useWorkflowCreation } from "@/features/workflows/hooks/useWorkflowCreation";

import { CommunityWorkflow, workflowApi } from "../api/workflowApi";
import BaseWorkflowCard from "./shared/BaseWorkflowCard";

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

  const footerContent = (
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
  );

  return (
    <BaseWorkflowCard
      title={localWorkflow.title}
      description={localWorkflow.description}
      steps={localWorkflow.steps}
      creator={{
        name: localWorkflow.creator.name,
        avatar: localWorkflow.creator.avatar,
      }}
      footerContent={footerContent}
    />
  );
}
