"use client";

import { Button } from "@heroui/button";
import { useDisclosure } from "@heroui/modal";
import { ExternalLink, RefreshCw, ZapIcon } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import UseCaseSection from "@/features/use-cases/components/UseCaseSection";

import Link from "next/link";
import { Workflow } from "../api/workflowApi";
import { useWorkflows } from "../hooks";
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

  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(
    null,
  );

  const { workflows, isLoading, error, refetch } = useWorkflows();

  // Handle workflow creation completion
  const handleWorkflowCreated = useCallback(() => {
    refetch(); // Refresh the list to show the new workflow
  }, [refetch]);

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
            <h3 className="text-xl font-medium text-zinc-300">
              No workflows yet
            </h3>
          </div>
          <Button color="primary" onPress={onOpen}>
            Create Your First Workflow
          </Button>
        </div>
      );
    }

    return (
      <div className="grid max-w-7xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3">
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
