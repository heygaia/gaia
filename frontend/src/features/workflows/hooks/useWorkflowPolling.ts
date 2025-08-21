import { useCallback, useState } from "react";

import { Workflow, workflowApi } from "../api/workflowApi";
import { usePolling } from "@/hooks/usePolling";

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
      const response = await workflowApi.getWorkflow(currentWorkflowId);
      return response.workflow;
    },
    {
      initialInterval: 1000, // Start with 1 second
      maxInterval: 10000, // Max 10 seconds
      maxAttempts: 120, // Up to 2 minutes of attempts
      maxDuration: 300000, // 5 minutes total
      enableBackoff: true,
      backoffMultiplier: 1.2,
      shouldStop: (workflow: Workflow) => {
        // Stop when workflow has steps and no error
        return workflow?.steps?.length > 0 && !workflow?.error_message;
      },
      isError: (workflow: Workflow) => !!workflow?.error_message,
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
