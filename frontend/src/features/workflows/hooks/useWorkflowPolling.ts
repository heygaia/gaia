import { useCallback,useEffect, useRef, useState } from "react";

import { Workflow,workflowApi } from "../api/workflowApi";

interface UseWorkflowPollingReturn {
  workflow: Workflow | null;
  isPolling: boolean;
  error: string | null;
  startPolling: (workflowId: string) => void;
  stopPolling: () => void;
  clearError: () => void;
}

export const useWorkflowPolling = (): UseWorkflowPollingReturn => {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const workflowIdRef = useRef<string | null>(null);
  const pollCountRef = useRef(0);

  const getPollingInterval = (pollCount: number): number => {
    // Start with 1 second, then gradually increase
    if (pollCount < 10) return 1000; // First 10 seconds: poll every 1s
    if (pollCount < 30) return 2000; // Next 40 seconds: poll every 2s
    if (pollCount < 60) return 5000; // Next 2.5 minutes: poll every 5s
    return 10000; // After that: poll every 10s
  };

  const shouldStopPolling = (status: string): boolean => {
    return ["ready", "failed", "active"].includes(status.toLowerCase());
  };

  const pollWorkflowStatus = useCallback(async (workflowId: string) => {
    try {
      const response = await workflowApi.getWorkflow(workflowId);
      const updatedWorkflow = response.workflow;

      setWorkflow(updatedWorkflow);
      setError(null);

      // Stop polling if workflow is in final state
      if (shouldStopPolling(updatedWorkflow.status)) {
        setIsPolling(false);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        return;
      }

      // Continue polling with adjusted interval
      pollCountRef.current++;
      const newInterval = getPollingInterval(pollCountRef.current);

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }

      intervalRef.current = setTimeout(() => {
        pollWorkflowStatus(workflowId);
      }, newInterval);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch workflow status";
      setError(errorMessage);

      // Continue polling even on error, but with longer interval
      pollCountRef.current++;
      const newInterval = Math.min(
        getPollingInterval(pollCountRef.current) * 2,
        30000,
      ); // Max 30s

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }

      intervalRef.current = setTimeout(() => {
        pollWorkflowStatus(workflowId);
      }, newInterval);
    }
  }, []);

  const startPolling = useCallback(
    (workflowId: string) => {
      if (workflowIdRef.current === workflowId && isPolling) {
        return; // Already polling this workflow
      }

      // Stop any existing polling
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      workflowIdRef.current = workflowId;
      pollCountRef.current = 0;
      setIsPolling(true);
      setError(null);

      // Start polling immediately
      pollWorkflowStatus(workflowId);
    },
    [pollWorkflowStatus, isPolling],
  );

  const stopPolling = useCallback(() => {
    setIsPolling(false);
    workflowIdRef.current = null;
    pollCountRef.current = 0;

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    workflow,
    isPolling,
    error,
    startPolling,
    stopPolling,
    clearError,
  };
};
