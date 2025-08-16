"use client";

import { Button } from "@heroui/button";
import { useDisclosure } from "@heroui/modal";
import { PlusIcon, RefreshCw } from "lucide-react";
import { useCallback, useEffect,useState } from "react";

import { useWorkflowPolling,useWorkflows } from "../hooks";
import CreateWorkflowModal from "./CreateWorkflowModal";
import WorkflowCard from "./WorkflowCard";
import { WorkflowListSkeleton } from "./WorkflowSkeletons";

export default function WorkflowPage() {
  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(
    null,
  );

  const { workflows, isLoading, error, refetch, addWorkflow, updateWorkflow } =
    useWorkflows();

  const {
    workflow: pollingWorkflow,
    isPolling,
    startPolling,
  } = useWorkflowPolling();

  // Handle workflow creation completion
  const handleWorkflowCreated = useCallback(
    (workflowId: string) => {
      setSelectedWorkflowId(workflowId);
      startPolling(workflowId);
      refetch(); // Refresh the list to show the new workflow
    },
    [startPolling, refetch],
  );

  // Update workflow from polling
  const handlePollingUpdate = useCallback(() => {
    if (pollingWorkflow && selectedWorkflowId) {
      updateWorkflow(selectedWorkflowId, pollingWorkflow);
    }
  }, [pollingWorkflow, selectedWorkflowId, updateWorkflow]);

  // Effect to handle polling updates
  useEffect(() => {
    handlePollingUpdate();
  }, [handlePollingUpdate]);

  const handleWorkflowClick = (workflowId: string) => {
    // TODO: Navigate to workflow detail page
    console.log("Navigate to workflow:", workflowId);
  };

  const renderWorkflowsGrid = () => {
    if (isLoading) {
      return <WorkflowListSkeleton />;
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center space-y-4 py-12">
          <p className="text-foreground-400">Failed to load workflows</p>
          <Button
            size="sm"
            variant="flat"
            onPress={refetch}
            startContent={<RefreshCw className="h-4 w-4" />}
          >
            Try Again
          </Button>
        </div>
      );
    }

    if (workflows.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center space-y-4 py-12">
          <div className="text-center">
            <h3 className="text-lg font-medium text-foreground-600">
              No workflows yet
            </h3>
            <p className="mt-1 text-sm text-foreground-400">
              Create your first workflow to get started
            </p>
          </div>
          <Button
            color="primary"
            onPress={onOpen}
            startContent={<PlusIcon className="h-4 w-4" />}
          >
            Create Your First Workflow
          </Button>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {workflows.map((workflow) => (
          <WorkflowCard
            key={workflow.id}
            workflow={workflow}
            onClick={() => handleWorkflowClick(workflow.id)}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="overflow-y-auto p-8 px-10">
      <div className="flex min-h-[50vh] flex-col gap-7">
        <div>
          <div className="flex w-full items-center justify-between">
            <div>
              <h1>Your Workflows</h1>
              <div className="text-foreground-400">
                Automate your tasks with AI-powered workflows
                {workflows.length > 0 && (
                  <span className="ml-2">
                    ({workflows.length} workflow
                    {workflows.length !== 1 ? "s" : ""})
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {workflows.length > 0 && (
                <Button
                  variant="flat"
                  size="sm"
                  isIconOnly
                  onPress={refetch}
                  isLoading={isLoading}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              )}
              <Button
                color="primary"
                size="sm"
                startContent={<PlusIcon width={16} height={16} />}
                onPress={onOpen}
              >
                Create
              </Button>
            </div>
          </div>
        </div>

        {renderWorkflowsGrid()}
      </div>

      <div className="flex min-h-[50vh] flex-col">
        <h1>Explore</h1>
        <div className="text-foreground-400">
          Discover workflow templates and community creations
        </div>
        {/* TODO: Add template gallery */}
      </div>

      <CreateWorkflowModal
        isOpen={isOpen}
        onOpenChange={onOpenChange}
        onWorkflowCreated={handleWorkflowCreated}
      />
    </div>
  );
}
