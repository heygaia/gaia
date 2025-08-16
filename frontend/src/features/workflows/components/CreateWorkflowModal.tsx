"use client";

import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Textarea } from "@heroui/input";
import { Modal, ModalBody, ModalContent, ModalFooter } from "@heroui/modal";
import { Tab, Tabs } from "@heroui/tabs";
import { Tooltip } from "@heroui/tooltip";
import { AlertCircle, CheckCircle, Info } from "lucide-react";
import React, { useEffect, useState } from "react";

import { useWorkflowCreation, useWorkflowPolling } from "../hooks";
import { ScheduleBuilder } from "./ScheduleBuilder";

interface WorkflowFormData {
  title: string;
  description: string;
  activeTab: "manual" | "schedule" | "email" | "calendar";
  trigger_config: {
    type: "manual" | "schedule" | "email" | "calendar" | "webhook";
    enabled: boolean;
    cron_expression?: string;
    timezone?: string;
    email_patterns?: string[];
    calendar_patterns?: string[];
  };
}

interface CreateWorkflowModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onWorkflowCreated?: (workflowId: string) => void;
}

export default function CreateWorkflowModal({
  isOpen,
  onOpenChange,
  onWorkflowCreated,
}: CreateWorkflowModalProps) {
  const {
    isCreating,
    error: creationError,
    createdWorkflow,
    createWorkflow,
    clearError: clearCreationError,
    reset: resetCreation,
  } = useWorkflowCreation();

  const {
    workflow: pollingWorkflow,
    startPolling,
    stopPolling,
  } = useWorkflowPolling();

  const [creationPhase, setCreationPhase] = useState<
    "form" | "creating" | "generating" | "success" | "error"
  >("form");
  const [formData, setFormData] = useState<WorkflowFormData>({
    title: "",
    description: "",
    activeTab: "manual",
    trigger_config: {
      type: "manual",
      enabled: true,
    },
  });

  // Remove unused trigger/integration logic (simplified workflow system)

  const updateFormData = (updates: Partial<WorkflowFormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      activeTab: "manual",
      trigger_config: {
        type: "manual",
        enabled: true,
      },
    });
    setCreationPhase("form");
    resetCreation();
    stopPolling();
    clearCreationError();
  };

  const handleCreate = async () => {
    if (!formData.title.trim()) return;

    setCreationPhase("creating");

    // Create the request object that matches the backend API
    const createRequest = {
      title: formData.title,
      description: formData.description,
      trigger_config: formData.trigger_config,
      generate_immediately: true,
    };

    const success = await createWorkflow(createRequest);

    if (success && createdWorkflow) {
      setCreationPhase("generating");
      startPolling(createdWorkflow.id);
      if (onWorkflowCreated) {
        onWorkflowCreated(createdWorkflow.id);
      }
    } else {
      setCreationPhase("error");
    }
  };

  const handleClose = () => {
    resetForm();
    onOpenChange(false);
  };

  // Handle polling results
  useEffect(() => {
    if (pollingWorkflow && creationPhase === "generating") {
      if (
        pollingWorkflow.status === "ready" ||
        pollingWorkflow.status === "active"
      ) {
        setCreationPhase("success");
        setTimeout(() => {
          handleClose();
        }, 2000); // Auto-close after 2 seconds
      } else if (pollingWorkflow.status === "failed") {
        setCreationPhase("error");
      }
    }
  }, [pollingWorkflow, creationPhase]);

  // Clean up when modal closes
  useEffect(() => {
    if (!isOpen) {
      resetForm();
    }
  }, [isOpen]);

  const renderTriggerTab = () => (
    <div className="w-full">
      <p className="text-sm text-foreground-500">
        This workflow will be triggered manually when you run it.
      </p>
    </div>
  );

  const renderScheduleTab = () => (
    <div className="w-full">
      <ScheduleBuilder
        value={formData.trigger_config.cron_expression || ""}
        onChange={(cronExpression) =>
          updateFormData({
            trigger_config: {
              ...formData.trigger_config,
              cron_expression: cronExpression,
            },
          })
        }
      />
    </div>
  );

  const renderStatusContent = () => {
    switch (creationPhase) {
      case "creating":
        return (
          <div className="flex flex-col items-center justify-center space-y-4 py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
            <div className="text-center">
              <h3 className="text-lg font-medium">Creating Workflow</h3>
              <p className="text-sm text-foreground-400">
                Setting up your workflow...
              </p>
            </div>
          </div>
        );

      case "generating":
        return (
          <div className="flex flex-col items-center justify-center space-y-4 py-8">
            <div className="animate-pulse">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
                <div className="h-6 w-6 animate-ping rounded-full bg-primary"></div>
              </div>
            </div>
            <div className="text-center">
              <h3 className="text-lg font-medium">Generating Steps</h3>
              <p className="text-sm text-foreground-400">
                AI is creating workflow steps for: "{formData.title}"
              </p>
              {pollingWorkflow && (
                <p className="mt-2 text-xs text-foreground-500">
                  Status: {pollingWorkflow.status}
                </p>
              )}
            </div>
          </div>
        );

      case "success":
        return (
          <div className="flex flex-col items-center justify-center space-y-4 py-8">
            <CheckCircle className="h-12 w-12 text-success" />
            <div className="text-center">
              <h3 className="text-lg font-medium text-success">
                Workflow Created!
              </h3>
              <p className="text-sm text-foreground-400">
                "{formData.title}" is ready to use
              </p>
              <p className="mt-2 text-xs text-foreground-500">
                {pollingWorkflow?.steps?.length || 0} steps generated
              </p>
            </div>
          </div>
        );

      case "error":
        return (
          <div className="flex flex-col items-center justify-center space-y-4 py-8">
            <AlertCircle className="h-12 w-12 text-danger" />
            <div className="text-center">
              <h3 className="text-lg font-medium text-danger">
                Creation Failed
              </h3>
              <p className="text-sm text-foreground-400">
                {creationError ||
                  "Something went wrong while creating the workflow"}
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) resetForm();
        onOpenChange(open);
      }}
      size="3xl"
      className="min-h-fit"
      scrollBehavior="inside"
      backdrop="blur"
    >
      <ModalContent>
        <ModalBody className="space-y-6 pt-8">
          {creationPhase === "form" ? (
            <>
              {/* Basic Information */}
              <div className="space-y-1">
                <Input
                  placeholder="Enter workflow name"
                  value={formData.title}
                  variant="underlined"
                  classNames={{
                    input: "font-semibold! text-4xl",
                    inputWrapper: "px-0",
                  }}
                  onChange={(e) => updateFormData({ title: e.target.value })}
                  isRequired
                />

                <Textarea
                  placeholder="Describe what this workflow does"
                  value={formData.description}
                  onChange={(e) =>
                    updateFormData({ description: e.target.value })
                  }
                  maxRows={3}
                  minRows={3}
                  variant="underlined"
                  className="text-sm"
                />
              </div>

              <div className="space-y-3">
                {/* Trigger/Schedule Tabs. rounded-2xl bg-zinc-800/50 p-1 pb-0 */}

                <div className="flex items-center gap-3">
                  <div className="flex min-w-26 items-center justify-between gap-1.5 text-sm font-medium text-foreground-500">
                    <span>When to Run</span>
                    <Tooltip
                      content={
                        <div className="px-1 py-2">
                          <p className="text-sm font-medium">When to Run</p>
                          <p className="mt-1 text-xs text-foreground-400">
                            Choose how your workflow will be activated:
                          </p>
                          <ul className="mt-2 space-y-1 text-xs text-foreground-400">
                            <li>
                              • <span className="font-medium">Manual:</span> Run
                              the workflow manually when you need it
                            </li>
                            <li>
                              • <span className="font-medium">Schedule:</span>{" "}
                              Run at specific times or intervals
                            </li>
                          </ul>
                        </div>
                      }
                      placement="top"
                      delay={500}
                    >
                      <Info className="h-3.5 w-3.5 cursor-help text-foreground-400 hover:text-foreground-600" />
                    </Tooltip>
                  </div>
                  <div>
                    <Tabs
                      color="primary"
                      classNames={{
                        tabList: "flex flex-row",
                        base: "flex items-start",
                        tabWrapper: "w-full",
                        panel: "min-w-full",
                      }}
                      selectedKey={formData.activeTab}
                      placement="start"
                      onSelectionChange={(key) => {
                        const tabKey = key as "manual" | "schedule";
                        updateFormData({
                          activeTab: tabKey,
                          trigger_config: {
                            ...formData.trigger_config,
                            type: tabKey,
                          },
                        });
                      }}
                    >
                      <Tab key="manual" title="Manual">
                        {renderTriggerTab()}
                      </Tab>
                      <Tab key="schedule" title="Schedule">
                        {renderScheduleTab()}
                      </Tab>
                    </Tabs>
                  </div>
                </div>
              </div>
            </>
          ) : (
            renderStatusContent()
          )}
        </ModalBody>

        <ModalFooter>
          {creationPhase === "form" ? (
            <>
              <Button variant="flat" onPress={handleClose}>
                Cancel
              </Button>
              <Button
                color="primary"
                onPress={handleCreate}
                isLoading={isCreating}
                isDisabled={
                  !formData.title ||
                  (formData.activeTab === "schedule" &&
                    !formData.trigger_config.cron_expression)
                }
              >
                {isCreating ? "Creating..." : "Create Workflow"}
              </Button>
            </>
          ) : creationPhase === "error" ? (
            <>
              <Button variant="flat" onPress={handleClose}>
                Cancel
              </Button>
              <Button color="primary" onPress={() => setCreationPhase("form")}>
                Try Again
              </Button>
            </>
          ) : creationPhase === "generating" ? (
            <Button variant="flat" onPress={handleClose} className="mx-auto">
              Close
            </Button>
          ) : null}
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
