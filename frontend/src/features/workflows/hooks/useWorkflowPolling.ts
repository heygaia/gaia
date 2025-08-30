import { useCallback, useState } from "react";

import { usePolling } from "@/hooks/usePolling";

import { Workflow, workflowApi } from "../api/workflowApi";

interface UseWorkflowPollingReturn {
  workflow: Workflow | null;
  isPolling: boolean;
  error: string | null;
  startPolling: (workflowId: string) => void;
  stopPolling: () => void;
  clearError: () => void;
}

export const useWorkflowPolling = (): UseWorkflowPollingReturn => {
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(
    null,
  );

  const {
    data: workflow,
    isPolling,
    error,
    startPolling: startGenericPolling,
    stopPolling,
    clearError,
  } = usePolling<Workflow>(
    async () => {
      if (!currentWorkflowId) {
        throw new Error("No workflow ID set for polling");
      }
      const response = await workflowApi.getWorkflow(currentWorkflowId, {
        silent: true,
      });
      return response.workflow;
    },
    {
      initialInterval: 1000, // Start with 1 second
      maxInterval: 10_000, // Max 10 seconds
      maxAttempts: 120, // Up to 2 minutes of attempts
      maxDuration: 300_000, // 5 minutes total
      enableBackoff: true,
      backoffMultiplier: 1.2,
      shouldStop: (workflow: Workflow) => {
        // Stop when workflow has steps (successful generation)
        return workflow?.steps?.length > 0;
      },
      isError: () => {
        // Only treat as error if we have error_message AND no steps AND it's been a while
        // This prevents premature error states during generation
        return false; // Let the modal handle error logic with more context
      },
      retryOnError: true,
      errorRetryMultiplier: 1.5,
    },
  );

  const startPolling = useCallback(
    (workflowId: string) => {
      if (!workflowId) {
        console.error("Cannot start polling: No workflow ID provided");
        return;
      }

      setCurrentWorkflowId(workflowId);
      startGenericPolling();
    },
    [startGenericPolling],
  );

  const stopPollingWrapper = useCallback(() => {
    setCurrentWorkflowId(null);
    stopPolling();
  }, [stopPolling]);

  return {
    workflow,
    isPolling,
    error,
    startPolling,
    stopPolling: stopPollingWrapper,
    clearError,
  };
};
