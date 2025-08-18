import React from "react";

import WorkflowModal from "./WorkflowModal";

interface CreateWorkflowModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onWorkflowCreated?: (workflowId: string) => void;
  onWorkflowListRefresh?: () => void;
}

export default function CreateWorkflowModal({
  isOpen,
  onOpenChange,
  onWorkflowCreated,
  onWorkflowListRefresh,
}: CreateWorkflowModalProps) {
  return (
    <WorkflowModal
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      onWorkflowSaved={onWorkflowCreated}
      onWorkflowListRefresh={onWorkflowListRefresh}
      mode="create"
    />
  );
}
