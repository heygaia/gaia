"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSendMessage } from "@/features/chat/hooks/useSendMessage";
import { formatToolName } from "@/features/chat/utils/chatUtils";
import { todoApi } from "@/features/todo/api/todoApi";
import {
  Workflow as WorkflowType,
  WorkflowStatus,
} from "@/types/features/todoTypes";

import WorkflowEmptyState from "./WorkflowEmptyState";
import WorkflowHeader from "./WorkflowHeader";
import WorkflowLoadingState from "./WorkflowLoadingState";
import WorkflowSteps from "./WorkflowSteps";

interface WorkflowSectionProps {
  workflow?: WorkflowType;
  isGenerating?: boolean;
  workflowStatus?: WorkflowStatus;
  todoId: string;
  todoTitle: string;
  todoDescription?: string;
  onGenerateWorkflow?: () => void;
  onWorkflowGenerated?: (workflow: WorkflowType) => void;
}

export default function WorkflowSection({
  workflow,
  isGenerating = false,
  workflowStatus = WorkflowStatus.NOT_STARTED,
  todoId,
  todoTitle,
  todoDescription: _todoDescription,
  onGenerateWorkflow,
  onWorkflowGenerated,
}: WorkflowSectionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [localIsGenerating, setLocalIsGenerating] = useState(
    isGenerating || workflowStatus === WorkflowStatus.GENERATING,
  );
  const router = useRouter();
  const sendMessage = useSendMessage();

  // Poll for workflow completion when generating
  useEffect(() => {
    if (!localIsGenerating || workflow) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await todoApi.getWorkflowStatus(todoId);

        if (status.has_workflow && status.workflow) {
          setLocalIsGenerating(false);
          onWorkflowGenerated?.(status.workflow);
          clearInterval(pollInterval);
        } else if (status.workflow_status === WorkflowStatus.FAILED) {
          setLocalIsGenerating(false);
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
      // Navigate to new chat
      router.push("/c");

      // Create workflow execution message
      const workflowMessage = `I want to execute a workflow for my todo: "${todoTitle}".

Here's the workflow plan:
${workflow.steps
  .map(
    (step, index) =>
      `${index + 1}. ${step.title} (${formatToolName(step.tool_name)}): ${step.description}`,
  )
  .join("\n")}

Please execute these steps in order and use the appropriate tools for each step.`;

      await sendMessage(workflowMessage);
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
      <WorkflowSteps steps={workflow.steps} />
    </div>
  );
}
