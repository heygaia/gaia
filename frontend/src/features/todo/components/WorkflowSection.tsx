"use client";

import { useEffect, useState } from "react";

import { todoApi } from "@/features/todo/api/todoApi";
import { workflowApi } from "@/features/workflows/api/workflowApi";
import {
  WorkflowStatus,
  Workflow as WorkflowType,
} from "@/types/features/todoTypes";

import {
  WorkflowEmptyState,
  WorkflowHeader,
  WorkflowLoadingState,
  WorkflowSteps,
} from "@/features/workflows/components";

interface WorkflowSectionProps {
  workflow?: WorkflowType;
  isGenerating?: boolean;
  workflowStatus?: WorkflowStatus;
  todoId: string;
  todoTitle: string;
  todoDescription?: string;
  onGenerateWorkflow?: () => void;
  onWorkflowGenerated?: (workflow: WorkflowType) => void;
  refreshTrigger?: number; // Add refresh trigger prop
  newWorkflow?: WorkflowType; // Direct workflow update prop
}

export default function WorkflowSection({
  workflow: initialWorkflow,
  isGenerating = false,
  workflowStatus: initialWorkflowStatus = WorkflowStatus.NOT_STARTED,
  todoId,
  todoTitle,
  todoDescription: _todoDescription,
  onGenerateWorkflow,
  onWorkflowGenerated,
  refreshTrigger,
  newWorkflow,
}: WorkflowSectionProps) {
  const [workflow, setWorkflow] = useState<WorkflowType | undefined>(
    initialWorkflow,
  );
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus>(
    initialWorkflowStatus,
  );
  const [isRunning, setIsRunning] = useState(false);
  const [localIsGenerating, setLocalIsGenerating] = useState(
    isGenerating || workflowStatus === WorkflowStatus.GENERATING,
  );

  // Fetch workflow on component mount and when refresh is triggered
  useEffect(() => {
    const fetchWorkflow = async () => {
      try {
        const status = await todoApi.getWorkflowStatus(todoId);
        if (status.has_workflow && status.workflow) {
          setWorkflow(status.workflow);
          setWorkflowStatus(status.workflow_status);
        } else {
          setWorkflow(undefined);
          setWorkflowStatus(WorkflowStatus.NOT_STARTED);
        }
      } catch (error) {
        console.error("Failed to fetch workflow:", error);
      }
    };

    fetchWorkflow();
  }, [todoId, refreshTrigger]); // Add refreshTrigger to dependencies

  // Handle direct workflow updates (for instant updates after generation)
  useEffect(() => {
    if (newWorkflow) {
      setWorkflow(newWorkflow);
      setWorkflowStatus(WorkflowStatus.COMPLETED);
      setLocalIsGenerating(false); // Ensure we stop generating state
      onWorkflowGenerated?.(newWorkflow);
    }
  }, [newWorkflow, onWorkflowGenerated]);

  // Poll for workflow completion when generating
  useEffect(() => {
    if (!localIsGenerating || workflow) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await todoApi.getWorkflowStatus(todoId);

        if (status.has_workflow && status.workflow) {
          setLocalIsGenerating(false);
          setWorkflow(status.workflow);
          setWorkflowStatus(status.workflow_status);
          onWorkflowGenerated?.(status.workflow);
          clearInterval(pollInterval);
        } else if (status.workflow_status === WorkflowStatus.FAILED) {
          setLocalIsGenerating(false);
          setWorkflowStatus(WorkflowStatus.FAILED);
          clearInterval(pollInterval);
          console.error("Workflow generation failed");
        }
      } catch (error) {
        console.error("Failed to check workflow status:", error);
      }
    }, 3000); // Poll every 3 seconds

    // Cleanup after 60 seconds to prevent infinite polling
    const timeoutId = setTimeout(() => {
      setLocalIsGenerating(false);
      clearInterval(pollInterval);
      console.warn("Workflow generation timed out");
    }, 60000);

    return () => {
      clearInterval(pollInterval);
      clearTimeout(timeoutId);
    };
  }, [localIsGenerating, workflow, todoId, onWorkflowGenerated]);

  // Update local generating state when props change
  useEffect(() => {
    setLocalIsGenerating(
      isGenerating || workflowStatus === WorkflowStatus.GENERATING,
    );
  }, [isGenerating, workflowStatus]);

  const handleRunWorkflow = async () => {
    if (!workflow) return;

    setIsRunning(true);
    try {
      // Execute the existing workflow directly
      const executionResponse = await workflowApi.executeWorkflow(workflow.id, {
        context: { source: "todo", todo_id: todoId },
      });

      console.log("Workflow execution started:", executionResponse);

      // Optionally, you could poll for status updates here
      // or redirect to a workflow status page
    } catch (error) {
      console.error("Failed to run workflow:", error);
    } finally {
      setIsRunning(false);
    }
  };

  if (localIsGenerating) {
    return <WorkflowLoadingState />;
  }

  if (!workflow) {
    return <WorkflowEmptyState onGenerateWorkflow={onGenerateWorkflow} />;
  }

  return (
    <div className="space-y-2">
      <WorkflowHeader
        isRunning={isRunning}
        onGenerateWorkflow={onGenerateWorkflow}
        onRunWorkflow={handleRunWorkflow}
      />
      <WorkflowSteps key={workflow.id} steps={workflow.steps} />
    </div>
  );
}
