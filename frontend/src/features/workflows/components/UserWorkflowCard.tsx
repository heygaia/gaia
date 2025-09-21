"use client";

import { Button } from "@heroui/button";
import { Play } from "lucide-react";
import { useState } from "react";

import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";
import { Workflow } from "@/features/workflows/api/workflowApi";

import BaseWorkflowCard from "./shared/BaseWorkflowCard";

interface UserWorkflowCardProps {
  workflow: Workflow;
}

export default function UserWorkflowCard({ workflow }: UserWorkflowCardProps) {
  const [isRunning, setIsRunning] = useState(false);
  const { selectWorkflow } = useWorkflowSelection();

  const handleRunWorkflow = async () => {
    if (isRunning) return;
    setIsRunning(true);
    try {
      selectWorkflow(workflow, { autoSend: true });
    } catch (error) {
      console.error("Error running workflow:", error);
    } finally {
      setIsRunning(false);
    }
  };

  const footerContent = (
    <div className="flex w-full flex-col gap-3">
      <Button
        color="primary"
        size="sm"
        startContent={<Play width={16} height={16} />}
        className="w-full"
        isLoading={isRunning}
        onPress={handleRunWorkflow}
      >
        Run Workflow
      </Button>
    </div>
  );

  return (
    <BaseWorkflowCard
      title={workflow.title}
      description={workflow.description}
      steps={workflow.steps}
      footerContent={footerContent}
      onClick={handleRunWorkflow}
      showArrowIcon={false}
    />
  );
}
