"use client";

import { Button } from "@heroui/button";
import { useDisclosure } from "@heroui/modal";
import { PlusIcon, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import UseCaseSection from "@/features/use-cases/components/UseCaseSection";

import { Workflow } from "../api/workflowApi";
import { useWorkflowPolling, useWorkflows } from "../hooks";
import CreateWorkflowModal from "./CreateWorkflowModal";
import EditWorkflowModal from "./EditWorkflowModal";
import WorkflowCard from "./WorkflowCard";
import { WorkflowListSkeleton } from "./WorkflowSkeletons";

export default function WorkflowPage() {
  const pageRef = useRef(null);
  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const {
    isOpen: isEditOpen,
    onOpen: onEditOpen,
    onOpenChange: onEditOpenChange,
  } = useDisclosure();

  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(
    null,
  );
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(
    null,
  );

  const { workflows, isLoading, error, refetch, updateWorkflow } =
    useWorkflows();

  const { workflow: pollingWorkflow, startPolling } = useWorkflowPolling();

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

  const handleWorkflowDeleted = useCallback(
    (workflowId: string) => {
      // TODO: Call delete API
      console.log("Workflow deleted:", workflowId);
      refetch(); // Refresh the list
    },
    [refetch],
  );

  const handleWorkflowClick = (workflowId: string) => {
    const workflow = workflows.find((w) => w.id === workflowId);
    if (workflow) {
      setSelectedWorkflow(workflow);
      onEditOpen();
    }
  };

  const renderWorkflowsGrid = () => {
    if (isLoading) return <WorkflowListSkeleton />;

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
      <div className="grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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
    <div
      className="space-y-10 overflow-y-auto p-4 sm:p-6 md:p-8 lg:px-10"
      ref={pageRef}
    >
      <div className="flex flex-col gap-6 md:gap-7">
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

      <div className="flex min-h-[50vh] flex-col gap-5">
        <div>
          <h1>Explore</h1>
          <div className="text-foreground-400">
            Discover workflow templates and community creations
          </div>
        </div>
        <UseCaseSection dummySectionRef={pageRef} hideUserWorkflows={true} />
      </div>

      <CreateWorkflowModal
        isOpen={isOpen}
        onOpenChange={onOpenChange}
        onWorkflowCreated={handleWorkflowCreated}
        onWorkflowListRefresh={refetch}
      />

      <EditWorkflowModal
        isOpen={isEditOpen}
        onOpenChange={onEditOpenChange}
        onWorkflowUpdated={() => refetch()}
        onWorkflowDeleted={handleWorkflowDeleted}
        onWorkflowListRefresh={refetch}
        workflow={selectedWorkflow}
      />
    </div>
  );
}
