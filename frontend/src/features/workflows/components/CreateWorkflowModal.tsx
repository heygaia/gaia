"use client";

import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Textarea } from "@heroui/input";
import { Modal, ModalBody, ModalContent, ModalFooter } from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Tab, Tabs } from "@heroui/tabs";
import { Tooltip } from "@heroui/tooltip";
import { AlertCircle, CheckCircle, Info } from "lucide-react";
import Image from "next/image";
import React, { useEffect, useState } from "react";

import { triggerOptions } from "../data/workflowData";
import { useWorkflowCreation, useWorkflowPolling } from "../hooks";
import { ScheduleBuilder } from "./ScheduleBuilder";

interface WorkflowFormData {
  title: string;
  description: string;
  activeTab: "manual" | "schedule" | "trigger";
  selectedTrigger: string;
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
    activeTab: "schedule",
    selectedTrigger: "",
    trigger_config: {
      type: "schedule",
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
      activeTab: "schedule",
      selectedTrigger: "",
      trigger_config: {
        type: "schedule",
        enabled: true,
      },
    });
    setCreationPhase("form");
    resetCreation();
    stopPolling();
    clearCreationError();
  };

  const handleCreate = async () => {
    if (!formData.title.trim() || !formData.description.trim()) return;

    setCreationPhase("creating");

    // Create the request object that matches the backend API
    const createRequest = {
      title: formData.title,
      description: formData.description,
      trigger_config: {
        ...formData.trigger_config,
        // Include selected trigger for future implementation
        selected_trigger: formData.selectedTrigger,
      },
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

  const renderTriggerTab = () => {
    const selectedTriggerOption = triggerOptions.find(
      (t) => t.id === formData.selectedTrigger,
    );

    return (
      <div className="w-full">
        <div className="w-full">
          <Select
            aria-label="Choose a custom trigger for your workflow"
            placeholder="Choose a trigger for your workflow"
            fullWidth
            className="w-screen max-w-xl"
            selectedKeys={
              formData.selectedTrigger ? [formData.selectedTrigger] : []
            }
            onSelectionChange={(keys) => {
              const selectedTrigger = Array.from(keys)[0] as string;
              updateFormData({
                selectedTrigger,
                trigger_config: {
                  ...formData.trigger_config,
                  type:
                    selectedTrigger === "gmail"
                      ? "email"
                      : selectedTrigger === "calendar"
                        ? "calendar"
                        : "webhook",
                },
              });
            }}
            startContent={
              selectedTriggerOption && (
                <Image
                  src={selectedTriggerOption.icon}
                  alt={selectedTriggerOption.name}
                  width={20}
                  height={20}
                  className="h-5 w-5 object-contain"
                />
              )
            }
          >
            {triggerOptions.map((trigger) => (
              <SelectItem
                key={trigger.id}
                startContent={
                  <Image
                    src={trigger.icon}
                    alt={trigger.name}
                    width={20}
                    height={20}
                    className="h-5 w-5 object-contain"
                  />
                }
                description={trigger.description}
              >
                {trigger.name}
              </SelectItem>
            ))}
          </Select>
        </div>

        {selectedTriggerOption && (
          <p className="mt-2 px-1 text-xs text-foreground-400">
            {selectedTriggerOption.description}
          </p>
        )}
      </div>
    );
  };

  const renderManualTab = () => (
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
      className="min-h-[50vh]"
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
                    input: "font-medium! text-4xl",
                    inputWrapper: "px-0",
                  }}
                  onChange={(e) => updateFormData({ title: e.target.value })}
                  isRequired
                />

                <Textarea
                  placeholder="Describe what this workflow should do when triggered"
                  value={formData.description}
                  onChange={(e) =>
                    updateFormData({ description: e.target.value })
                  }
                  minRows={4}
                  variant="underlined"
                  className="text-sm"
                  isRequired
                />
              </div>

              <div className="space-y-3">
                {/* Trigger/Schedule Tabs. rounded-2xl bg-zinc-800/50 p-1 pb-0 */}

                <div className="flex items-start gap-3">
                  <div className="mt-2.5 flex min-w-26 items-center justify-between gap-1.5 text-sm font-medium text-foreground-500">
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
                            <li>
                              • <span className="font-medium">Trigger:</span>{" "}
                              Run when external events occur (coming soon)
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
                  <div className="w-full">
                    <Tabs
                      color="primary"
                      classNames={{
                        tabList: "flex flex-row",
                        base: "flex items-start",
                        tabWrapper: "w-full",
                        panel: "min-w-full",
                      }}
                      className="w-full"
                      selectedKey={formData.activeTab}
                      onSelectionChange={(key) => {
                        const tabKey = key as "manual" | "schedule" | "trigger";
                        updateFormData({
                          activeTab: tabKey,
                          trigger_config: {
                            ...formData.trigger_config,
                            type: tabKey === "trigger" ? "email" : tabKey,
                          },
                        });
                      }}
                    >
                      <Tab key="schedule" title="Schedule">
                        {renderScheduleTab()}
                      </Tab>
                      <Tab key="trigger" title="Trigger">
                        {renderTriggerTab()}
                      </Tab>
                      <Tab key="manual" title="Manual">
                        {renderManualTab()}
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
                  !formData.title.trim() ||
                  !formData.description.trim() ||
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
