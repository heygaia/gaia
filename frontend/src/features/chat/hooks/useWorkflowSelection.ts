import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Workflow } from "@/features/workflows/api/workflowApi";

interface SelectedWorkflowData {
  id: string;
  title: string;
  description: string;
  steps: Array<{
    id: string;
    title: string;
    description: string;
    tool_name: string;
    tool_category: string;
  }>;
}

interface WorkflowSelectionOptions {
  autoSend?: boolean;
}

export const useWorkflowSelection = () => {
  const [selectedWorkflow, setSelectedWorkflow] =
    useState<SelectedWorkflowData | null>(null);
  const router = useRouter();

  // Check for stored workflow on mount
  useEffect(() => {
    const storedWorkflow = localStorage.getItem("selectedWorkflow");
    if (storedWorkflow) {
      try {
        const workflowData = JSON.parse(storedWorkflow);
        setSelectedWorkflow(workflowData);
        // Clean up localStorage after loading
        localStorage.removeItem("selectedWorkflow");
      } catch (error) {
        console.error("Failed to parse stored workflow:", error);
        localStorage.removeItem("selectedWorkflow");
      }
    }
  }, []);

  const selectWorkflow = (
    workflow: Workflow | SelectedWorkflowData,
    options?: WorkflowSelectionOptions,
  ) => {
    let workflowData: SelectedWorkflowData;

    // Check if it's already in the correct format
    if ("trigger_config" in workflow) {
      // It's a full Workflow object, extract the needed fields
      workflowData = {
        id: workflow.id,
        title: workflow.title,
        description: workflow.description,
        steps: workflow.steps.map((step) => ({
          id: step.id,
          title: step.title,
          description: step.description,
          tool_name: step.tool_name,
          tool_category: step.tool_category,
        })),
      };
    } else {
      // It's already a SelectedWorkflowData object
      workflowData = workflow;
    }

    // Store in localStorage for persistence across navigation
    localStorage.setItem("selectedWorkflow", JSON.stringify(workflowData));

    // Store auto-send flag if requested for backward compatibility
    if (options?.autoSend) {
      localStorage.setItem("workflowAutoSend", "true");
    }

    // Navigate to chat page
    router.push("/c");
  };

  const clearSelectedWorkflow = () => {
    setSelectedWorkflow(null);
    localStorage.removeItem("selectedWorkflow");
    localStorage.removeItem("workflowAutoSend");
  };

  return {
    selectedWorkflow,
    selectWorkflow,
    clearSelectedWorkflow,
    setSelectedWorkflow,
  };
};
