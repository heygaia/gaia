import { usePathname, useRouter } from "next/navigation";
import { useCallback } from "react";

import { Workflow } from "@/features/workflows/api/workflowApi";
import {
  SelectedWorkflowData,
  useWorkflowSelectionStore,
  WorkflowSelectionOptions,
} from "@/stores/workflowSelectionStore";

export { type SelectedWorkflowData, type WorkflowSelectionOptions };

export const useWorkflowSelection = () => {
  const {
    selectedWorkflow,
    selectWorkflow: storeSelectWorkflow,
    clearSelectedWorkflow,
    setSelectedWorkflow,
  } = useWorkflowSelectionStore();
  const router = useRouter();
  const pathname = usePathname();

  const selectWorkflow = useCallback(
    (
      workflow: Workflow | SelectedWorkflowData,
      options?: WorkflowSelectionOptions,
    ) => {
      // Use store to persist the workflow selection
      storeSelectWorkflow(workflow, options);

      // Navigate to chat page if not already there
      if (pathname !== "/c") {
        router.push("/c");
      }
    },
    [storeSelectWorkflow, pathname, router],
  );

  return {
    selectedWorkflow,
    selectWorkflow,
    clearSelectedWorkflow,
    setSelectedWorkflow,
  };
};
