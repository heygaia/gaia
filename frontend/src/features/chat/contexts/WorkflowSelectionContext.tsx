"use client";

import React, { createContext, useContext, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

import { Workflow } from "@/features/workflows/api/workflowApi";

export interface SelectedWorkflowData {
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

interface WorkflowSelectionContextType {
  selectedWorkflow: SelectedWorkflowData | null;
  selectWorkflow: (
    workflow: Workflow | SelectedWorkflowData,
    options?: WorkflowSelectionOptions,
  ) => void;
  clearSelectedWorkflow: () => void;
  setSelectedWorkflow: (workflow: SelectedWorkflowData | null) => void;
}

const WorkflowSelectionContext = createContext<
  WorkflowSelectionContextType | undefined
>(undefined);

export const WorkflowSelectionProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const [selectedWorkflow, setSelectedWorkflow] =
    useState<SelectedWorkflowData | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  const selectWorkflow = (
    workflow: Workflow | SelectedWorkflowData,
    options?: WorkflowSelectionOptions,
  ) => {
    const workflowData: SelectedWorkflowData =
      "trigger_config" in workflow
        ? {
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
          }
        : workflow;

    // Store auto-send flag if requested
    if (options?.autoSend) localStorage.setItem("workflowAutoSend", "true");

    // Set workflow in context (persists across navigation now)
    setSelectedWorkflow(workflowData);

    // Navigate to chat page if not already there
    if (pathname !== "/c") router.push("/c");
  };

  const clearSelectedWorkflow = () => {
    setSelectedWorkflow(null);
    localStorage.removeItem("selectedWorkflow");
    localStorage.removeItem("workflowAutoSend");
  };

  return (
    <WorkflowSelectionContext.Provider
      value={{
        selectedWorkflow,
        selectWorkflow,
        clearSelectedWorkflow,
        setSelectedWorkflow,
      }}
    >
      {children}
    </WorkflowSelectionContext.Provider>
  );
};

export const useWorkflowSelection = () => {
  const context = useContext(WorkflowSelectionContext);
  if (context === undefined) {
    throw new Error(
      "useWorkflowSelection must be used within a WorkflowSelectionProvider",
    );
  }
  return context;
};
