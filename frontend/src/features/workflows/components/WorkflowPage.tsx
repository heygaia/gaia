"use client";

import { Button } from "@heroui/button";
import { useDisclosure } from "@heroui/modal";
import { ExternalLink, PlusIcon, RefreshCw, ZapIcon } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import UseCaseSection from "@/features/use-cases/components/UseCaseSection";

import { Workflow } from "../api/workflowApi";
import { useWorkflowPolling, useWorkflows } from "../hooks";
import CreateWorkflowModal from "./CreateWorkflowModal";
import EditWorkflowModal from "./EditWorkflowModal";
import WorkflowCard from "./WorkflowCard";
import { WorkflowListSkeleton } from "./WorkflowSkeletons";
import { OpenInNewWindowIcon } from "@radix-ui/react-icons";
import Link from "next/link";

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
        <div className="flex w-full flex-col items-center justify-center">
          <h1 className="mb-2 text-5xl font-normal">Explore Workflows</h1>
          <p className="mx-auto max-w-3xl text-lg text-zinc-500">
            Your workflows and community creations in one place
          </p>

          <div className="mt-3 flex justify-center gap-2">
            {workflows.length > 0 && (
              <Button
                variant="flat"
                size="sm"
                isIconOnly
                onPress={refetch}
                isLoading={isLoading}
                className="text-zinc-400"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            )}

            <Link href={"/use-cases"}>
              <Button
                variant="flat"
                size="sm"
                className="text-zinc-400"
                endContent={<ExternalLink width={16} height={16} />}
              >
                Community Marketplace
              </Button>
            </Link>

            <Button
              color="primary"
              size="sm"
              variant="flat"
              onPress={onOpen}
              className="text-primary"
              endContent={<ZapIcon width={14} height={14} />}
            >
              Create
            </Button>
          </div>
        </div>

        {renderWorkflowsGrid()}
      </div>

      <div className="mt-12 flex min-h-[50vh] flex-col gap-5">
        <div className="text-center">
          <h1 className="mb-2 text-4xl font-normal">
            Published by The Community
          </h1>
          <p className="mx-auto max-w-3xl text-lg text-zinc-500">
            Discover what others are building with GAIA
          </p>
        </div>
        <UseCaseSection dummySectionRef={pageRef} hideUserWorkflows={false} />
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
