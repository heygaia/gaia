import { useState } from "react";

import {
  CreateWorkflowRequest,
  Workflow,
  workflowApi,
} from "../api/workflowApi";

export const useWorkflowCreation = (): UseWorkflowCreationReturn => {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdWorkflow, setCreatedWorkflow] = useState<Workflow | null>(null);

  const createWorkflow = async (
    request: CreateWorkflowRequest,
  ): Promise<{ success: boolean; workflow?: Workflow }> => {
    try {
      setIsCreating(true);
      setError(null);

      const response = await workflowApi.createWorkflow(request);

      setCreatedWorkflow(response.workflow);
      return { success: true, workflow: response.workflow };
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create workflow";
      setError(errorMessage);
      return { success: false };
    } finally {
      setIsCreating(false);
    }
  };

  const clearError = () => setError(null);

  const reset = () => {
    setIsCreating(false);
    setError(null);
    setCreatedWorkflow(null);
  };

  return {
    isCreating,
    error,
    createdWorkflow,
    createWorkflow,
    clearError,
    reset,
  };
};

interface UseWorkflowCreationReturn {
  isCreating: boolean;
  error: string | null;
  createdWorkflow: Workflow | null;
  createWorkflow: (
    request: CreateWorkflowRequest,
  ) => Promise<{ success: boolean; workflow?: Workflow }>;
  clearError: () => void;
  reset: () => void;
}
