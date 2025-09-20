"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import {
  Dropdown,
  DropdownItem,
  DropdownMenu,
  DropdownTrigger,
} from "@heroui/dropdown";
import { Input, Textarea } from "@heroui/input";
import { Modal, ModalBody, ModalContent } from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Switch } from "@heroui/switch";
import { Tab, Tabs } from "@heroui/tabs";
import { Tooltip } from "@heroui/tooltip";
import { DotsVerticalIcon } from "@radix-ui/react-icons";
import {
  AlertCircle,
  ChevronDown,
  ExternalLink,
  Info,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { CheckmarkCircle02Icon } from "@/components/shared/icons";
import CustomSpinner from "@/components/ui/shadcn/spinner";
import { useWorkflowSelection } from "@/features/chat/hooks/useWorkflowSelection";

import { Workflow, workflowApi } from "../api/workflowApi";
import { triggerOptions } from "../data/workflowData";
import { useWorkflowCreation, useWorkflowPolling } from "../hooks";
import { ScheduleBuilder } from "./ScheduleBuilder";
import WorkflowSteps from "./shared/WorkflowSteps";

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

interface WorkflowModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onWorkflowSaved?: (workflowId: string) => void;
  onWorkflowDeleted?: (workflowId: string) => void;
  onWorkflowListRefresh?: () => void;
  mode: "create" | "edit";
  existingWorkflow?: Workflow | null;
}

export default function WorkflowModal({
  isOpen,
  onOpenChange,
  onWorkflowSaved,
  onWorkflowDeleted,
  onWorkflowListRefresh,
  mode,
  existingWorkflow,
}: WorkflowModalProps) {
  const router = useRouter();
  const {
    isCreating,
    error: creationError,
    createWorkflow,
    clearError: clearCreationError,
    reset: resetCreation,
  } = useWorkflowCreation();

  const { isPolling, startPolling, stopPolling } = useWorkflowPolling();

  const { selectWorkflow } = useWorkflowSelection();

  // Single source of truth for workflow data
  const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(null);

  // Manage the single workflow state from all sources
  useEffect(() => {
    if (existingWorkflow) {
      setCurrentWorkflow(existingWorkflow);
    } else {
      setCurrentWorkflow(null);
    }
  }, [existingWorkflow]);

  // Update currentWorkflow from polling results (for regeneration)
  const { workflow: pollingWorkflow } = useWorkflowPolling();
  useEffect(() => {
    if (pollingWorkflow && currentWorkflow?.id === pollingWorkflow.id) {
      // Only update if it's the same workflow being polled
      setCurrentWorkflow(pollingWorkflow);
    }
  }, [pollingWorkflow, currentWorkflow?.id]);

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

  // State for workflow activation toggle
  const [isActivated, setIsActivated] = useState(true);
  const [isTogglingActivation, setIsTogglingActivation] = useState(false);

  // State for step regeneration
  const [isRegeneratingSteps, setIsRegeneratingSteps] = useState(false);
  useState<string>("");
  const [regenerationError, setRegenerationError] = useState<string | null>(
    null,
  );

  // State for countdown close timer
  const [countdown, setCountdown] = useState<number>(0);
  const [countdownInterval, setCountdownInterval] =
    useState<NodeJS.Timeout | null>(null);

  // Regeneration reason options (only for existing workflows)
  const regenerationReasons = [
    {
      key: "alternative",
      label: "Generate alternative approach",
      description: "Create a different way to achieve the same goal",
    },
    {
      key: "efficient",
      label: "Make more efficient",
      description: "Optimize steps for better performance",
    },
    {
      key: "detailed",
      label: "Add more detail",
      description: "Include more comprehensive steps",
    },
    {
      key: "simplified",
      label: "Simplify workflow",
      description: "Reduce complexity and number of steps",
    },
    {
      key: "tools",
      label: "Use different tools",
      description: "Try different tools for the same tasks",
    },
    {
      key: "reorder",
      label: "Reorder steps",
      description: "Change the sequence of operations",
    },
  ];

  // Handle initial step generation (for empty workflows)
  const handleInitialGeneration = () => {
    handleRegenerateSteps("Generate workflow steps", false); // Don't force different tools for initial generation
  };

  // Initialize form data based on mode and currentWorkflow
  useEffect(() => {
    if (mode === "edit" && currentWorkflow) {
      setFormData({
        title: currentWorkflow.title,
        description: currentWorkflow.description,
        activeTab:
          currentWorkflow.trigger_config.type === "email" ||
          currentWorkflow.trigger_config.type === "calendar" ||
          currentWorkflow.trigger_config.type === "webhook"
            ? "trigger"
            : (currentWorkflow.trigger_config.type as "manual" | "schedule"),
        selectedTrigger:
          currentWorkflow.trigger_config.type === "email"
            ? "gmail"
            : currentWorkflow.trigger_config.type === "calendar"
              ? "calendar"
              : "",
        trigger_config: currentWorkflow.trigger_config,
      });
      // Initialize activation state from current workflow
      setIsActivated(currentWorkflow.activated);
    } else {
      // Reset to default for create mode
      setFormData({
        title: "",
        description: "",
        activeTab: "schedule",
        selectedTrigger: "",
        trigger_config: {
          type: "schedule",
          enabled: true,
          cron_expression: "0 9 * * *", // Default: daily at 9 AM
        },
      });
      // Reset activation state for create mode
      setIsActivated(true);
    }
  }, [mode, currentWorkflow, isOpen]);

  const updateFormData = (updates: Partial<WorkflowFormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  const resetForm = useCallback(() => {
    setFormData({
      title: "",
      description: "",
      activeTab: "schedule",
      selectedTrigger: "",
      trigger_config: {
        type: "schedule",
        enabled: true,
        cron_expression: "0 9 * * *", // Default: daily at 9 AM
      },
    });
    setCreationPhase("form");
    resetCreation();
    stopPolling();
    clearCreationError();
  }, [resetCreation, stopPolling, clearCreationError]);

  const handleSave = async () => {
    if (!formData.title.trim() || !formData.description.trim()) return;

    if (mode === "create") {
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

      const result = await createWorkflow(createRequest);

      if (result.success && result.workflow) {
        // Update currentWorkflow with the newly created workflow
        setCurrentWorkflow(result.workflow);
        setCreationPhase("generating");
        startPolling(result.workflow.id);
        if (onWorkflowSaved) {
          onWorkflowSaved(result.workflow.id);
        }
        // Refresh workflow list after creation
        if (onWorkflowListRefresh) {
          onWorkflowListRefresh();
        }
      } else {
        setCreationPhase("error");
      }
    } else {
      // Edit mode - update the existing workflow
      if (!currentWorkflow) return;

      try {
        const updateRequest = {
          title: formData.title,
          description: formData.description,
          trigger_config: {
            ...formData.trigger_config,
            selected_trigger: formData.selectedTrigger,
          },
        };

        const updatedWorkflow = await workflowApi.updateWorkflow(
          currentWorkflow.id,
          updateRequest,
        );

        // Update currentWorkflow with the updated data
        if (updatedWorkflow) {
          setCurrentWorkflow({
            ...currentWorkflow,
            ...updateRequest,
          });
        }

        if (onWorkflowSaved) {
          onWorkflowSaved(currentWorkflow.id);
        }
        // Refresh workflow list after update
        if (onWorkflowListRefresh) {
          onWorkflowListRefresh();
        }
        handleClose();
      } catch (error) {
        console.error("Failed to update workflow:", error);
      }
    }
  };

  const handleClose = useCallback(() => {
    // Clear countdown interval if active
    if (countdownInterval) {
      clearInterval(countdownInterval);
      setCountdownInterval(null);
    }
    setCountdown(0);
    resetForm();
    onOpenChange(false);
  }, [countdownInterval, resetForm, onOpenChange]);

  const handleDelete = async () => {
    if (mode === "edit" && existingWorkflow) {
      try {
        // Call the actual delete API
        await workflowApi.deleteWorkflow(existingWorkflow.id);

        if (onWorkflowDeleted) {
          onWorkflowDeleted(existingWorkflow.id);
        }
        // Refresh workflow list after deletion
        if (onWorkflowListRefresh) {
          onWorkflowListRefresh();
        }
        handleClose();
      } catch (error) {
        console.error("Failed to delete workflow:", error);
      }
    }
  };

  // Handle activation toggle
  const handleActivationToggle = async (newActivated: boolean) => {
    if (mode !== "edit" || !currentWorkflow) return;

    setIsTogglingActivation(true);
    try {
      if (newActivated) {
        await workflowApi.activateWorkflow(currentWorkflow.id);
      } else {
        await workflowApi.deactivateWorkflow(currentWorkflow.id);
      }

      // Update currentWorkflow activation state
      setCurrentWorkflow({
        ...currentWorkflow,
        activated: newActivated,
      });
      setIsActivated(newActivated);

      // Refresh workflow list after activation/deactivation
      if (onWorkflowListRefresh) {
        onWorkflowListRefresh();
      }
    } catch (error) {
      console.error("Failed to toggle workflow activation:", error);
    } finally {
      setIsTogglingActivation(false);
    }
  };

  // Handle step regeneration
  const handleRegenerateSteps = async (
    reason: string = "Generate alternative workflow approach",
    forceDifferentTools: boolean = true,
  ) => {
    if (mode !== "edit" || !currentWorkflow) return;

    setIsRegeneratingSteps(true);
    setRegenerationError(null); // Clear any previous errors

    try {
      // Call the enhanced regenerate steps API with selected reason
      const result = await workflowApi.regenerateWorkflowSteps(
        currentWorkflow.id,
        {
          reason,
          force_different_tools: forceDifferentTools,
        },
      );

      // Start polling to see the regenerated workflow
      startPolling(currentWorkflow.id);

      // Refresh the workflow data in the parent component
      if (onWorkflowSaved) onWorkflowSaved(currentWorkflow.id);

      // Refresh workflow list after regeneration
      if (onWorkflowListRefresh) onWorkflowListRefresh();

      console.log("Steps regeneration started:", result.message);
    } catch (error) {
      console.error("Failed to start workflow regeneration:", error);

      // Extract error message for user display
      const errorMessage =
        error instanceof Error
          ? error.message
          : typeof error === "string"
            ? error
            : "Failed to start workflow regeneration";

      setRegenerationError(errorMessage);
      setIsRegeneratingSteps(false);
    }
    // Note: Don't set isRegeneratingSteps to false here - let polling handle it
  };

  // Handle regeneration with specific reason
  const handleRegenerateWithReason = (reasonKey: string) => {
    const reason = regenerationReasons.find((r) => r.key === reasonKey);
    if (reason) {
      handleRegenerateSteps(reason.label, true); // Always force different tools for regeneration
    }
  };

  // Handle workflow execution
  const handleRunWorkflow = async () => {
    if (mode !== "edit" || !existingWorkflow) return;

    try {
      selectWorkflow(existingWorkflow, { autoSend: true });

      // Close the modal after navigation starts
      onOpenChange(false);

      console.log(
        "Workflow selected for manual execution in chat with auto-send",
      );
    } catch (error) {
      console.error("Failed to select workflow for execution:", error);
    }
  };

  // Handle polling results (only for create mode)
  useEffect(() => {
    if (
      mode === "create" &&
      currentWorkflow &&
      creationPhase === "generating"
    ) {
      // Check if workflow has steps and is ready
      const hasSteps =
        currentWorkflow.steps && currentWorkflow.steps.length > 0;

      if (hasSteps) {
        setCreationPhase("success");
        stopPolling(); // Stop polling on success

        // Refresh workflow list when steps are generated successfully
        if (onWorkflowListRefresh) {
          onWorkflowListRefresh();
        }

        // Start countdown
        setCountdown(5); // 5 seconds countdown
        const interval = setInterval(() => {
          setCountdown((prev) => {
            if (prev <= 1) {
              clearInterval(interval);
              handleClose();
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
        setCountdownInterval(interval);

        return;
      }

      // For error handling, we'll rely on polling timeout rather than immediate error_message
      // This prevents showing error for temporary generation issues
      // The polling hook will stop after maxDuration (5 minutes) or maxAttempts (120)
    }
  }, [
    currentWorkflow,
    creationPhase,
    stopPolling,
    mode,
    handleClose,
    onWorkflowListRefresh,
  ]);

  // Handle polling timeout/completion for error states
  useEffect(() => {
    if (mode === "create" && !isPolling && creationPhase === "generating") {
      // Polling stopped but we're still in generating phase
      // Check if we have steps or if it's an error case
      if (currentWorkflow?.steps && currentWorkflow.steps.length > 0) {
        setCreationPhase("success");

        // Refresh workflow list when steps are generated successfully
        if (onWorkflowListRefresh) {
          onWorkflowListRefresh();
        }

        setTimeout(() => {
          handleClose();
        }, 2000);
      } else {
        // No steps after polling completed - this is an error
        setCreationPhase("error");
        setTimeout(() => {
          handleClose();
        }, 3000);
      }
    }
  }, [
    isPolling,
    creationPhase,
    currentWorkflow,
    mode,
    onWorkflowListRefresh,
    handleClose,
  ]);

  // Handle regeneration completion for edit mode
  useEffect(() => {
    if (mode === "edit" && isRegeneratingSteps && currentWorkflow) {
      // Check if we have new steps (indicating regeneration completed successfully)
      const hasNewSteps =
        currentWorkflow.steps && currentWorkflow.steps.length > 0;

      if (hasNewSteps) {
        // Show success toast
        toast.success("Workflow steps regenerated successfully!", {
          description: `${currentWorkflow.steps?.length || 0} new steps created`,
          duration: 3000,
        });

        // Regeneration completed - just stop the loading state
        setIsRegeneratingSteps(false);
        setRegenerationError(null);
        stopPolling();
      }
    }
  }, [currentWorkflow, isRegeneratingSteps, stopPolling, mode]);

  // Timeout mechanism for regeneration
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    if (isRegeneratingSteps) {
      // Set a 60-second timeout for regeneration
      timeoutId = setTimeout(() => {
        setRegenerationError(
          "Regeneration is taking longer than expected. Please try again.",
        );
        setIsRegeneratingSteps(false);
        stopPolling();

        toast.error("Regeneration timeout", {
          description: "The regeneration is taking too long. Please try again.",
          duration: 5000,
        });
      }, 60000); // 60 seconds timeout
    }

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [isRegeneratingSteps, stopPolling]);

  // Clean up when modal closes
  useEffect(() => {
    if (!isOpen) {
      // Clear countdown interval if active
      if (countdownInterval) {
        clearInterval(countdownInterval);
        setCountdownInterval(null);
      }
      setCountdown(0);
      // Don't call resetForm here - it's already called in onOpenChange
    }
  }, [isOpen, countdownInterval]);

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
          <p className="mt-2 px-1 text-xs text-zinc-500">
            {selectedTriggerOption.description}
          </p>
        )}
      </div>
    );
  };

  const renderManualTab = () => (
    <div className="w-full">
      <p className="text-sm text-zinc-500">
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

  const getButtonText = () => {
    if (mode === "edit") return isCreating ? "Saving..." : "Save Changes";
    return isCreating ? "Creating..." : "Create Workflow";
  };

  return (
    <Modal
      key={currentWorkflow?.id || "new-workflow"}
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) resetForm();
        onOpenChange(open);
      }}
      hideCloseButton
      size={mode === "create" ? "3xl" : "4xl"}
      className={`max-h-[70vh] ${mode !== "create" ? "min-w-[80vw]" : ""}`}
      backdrop="blur"
    >
      <ModalContent>
        <ModalBody className="max-h-full space-y-6 overflow-hidden pt-8">
          {creationPhase === "form" ? (
            <div className="flex h-full min-h-0 gap-8">
              <div className="flex min-h-0 flex-1 flex-col">
                <div className="min-h-0 flex-1 space-y-6 overflow-y-auto">
                  <div className="flex items-center gap-3">
                    <Input
                      autoFocus
                      placeholder={
                        mode === "edit"
                          ? "Edit workflow name"
                          : "Enter workflow name"
                      }
                      value={formData.title}
                      variant="underlined"
                      classNames={{
                        input: "font-medium! text-4xl",
                        inputWrapper: "px-0",
                      }}
                      onChange={(e) =>
                        updateFormData({ title: e.target.value })
                      }
                      isRequired
                      className="flex-1"
                    />

                    {/* Action dropdown for edit mode */}
                    {mode === "edit" && (
                      <Dropdown placement="bottom-end" className="max-w-60">
                        <DropdownTrigger>
                          <Button variant="flat" size="sm" isIconOnly>
                            <DotsVerticalIcon />
                          </Button>
                        </DropdownTrigger>
                        <DropdownMenu>
                          <DropdownItem
                            key="publish"
                            startContent={
                              <Play className="relative top-1 h-4 w-4" />
                            }
                            classNames={{
                              description: "text-wrap",
                              base: "items-start!",
                            }}
                            description={
                              currentWorkflow?.is_public
                                ? "Remove from community marketplace"
                                : "Share to community marketplace"
                            }
                            onPress={async () => {
                              if (!currentWorkflow?.id) return;

                              try {
                                if (currentWorkflow.is_public) {
                                  await workflowApi.unpublishWorkflow(
                                    currentWorkflow.id,
                                  );
                                  setCurrentWorkflow((prev) =>
                                    prev ? { ...prev, is_public: false } : null,
                                  );
                                } else {
                                  await workflowApi.publishWorkflow(
                                    currentWorkflow.id,
                                  );
                                  setCurrentWorkflow((prev) =>
                                    prev ? { ...prev, is_public: true } : null,
                                  );
                                }
                              } catch (error) {
                                console.error(
                                  "Error publishing/unpublishing workflow:",
                                  error,
                                );
                              }
                            }}
                          >
                            {currentWorkflow?.is_public
                              ? "Unpublish Workflow"
                              : "Publish Workflow"}
                          </DropdownItem>

                          {/* Conditionally render marketplace item */}
                          {currentWorkflow?.is_public ? (
                            <DropdownItem
                              key="marketplace"
                              startContent={
                                <ExternalLink className="h-4 w-4" />
                              }
                              classNames={{
                                description: "text-wrap",
                                base: "items-start!",
                              }}
                              description="Open community marketplace"
                              onPress={() => {
                                router.push("/use-cases#community-section");
                              }}
                            >
                              View on Marketplace
                            </DropdownItem>
                          ) : (
                            <></>
                          )}

                          <DropdownItem
                            key="delete"
                            color="danger"
                            startContent={<Trash2 className="h-4 w-4" />}
                            classNames={{
                              description: "text-wrap",
                              base: "items-start!",
                            }}
                            description="Permanently delete this workflow"
                            onPress={handleDelete}
                          >
                            Delete Workflow
                          </DropdownItem>
                        </DropdownMenu>
                      </Dropdown>
                    )}
                  </div>

                  {/* Trigger/Schedule Configuration */}
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="mt-2.5 flex min-w-26 items-center justify-between gap-1.5 text-sm font-medium text-zinc-400">
                        <span>When to Run</span>
                        <Tooltip
                          content={
                            <div className="px-1 py-2">
                              <p className="text-sm font-medium">When to Run</p>
                              <p className="mt-1 text-xs text-zinc-400">
                                Choose how your workflow will be activated:
                              </p>
                              <ul className="mt-2 space-y-1 text-xs text-zinc-400">
                                <li>
                                  • <span className="font-medium">Manual:</span>{" "}
                                  Run the workflow manually when you need it
                                </li>
                                <li>
                                  •{" "}
                                  <span className="font-medium">Schedule:</span>{" "}
                                  Run at specific times or intervals
                                </li>
                                <li>
                                  •{" "}
                                  <span className="font-medium">Trigger:</span>{" "}
                                  Run when external events occur (coming soon)
                                </li>
                              </ul>
                            </div>
                          }
                          placement="top"
                          delay={500}
                        >
                          <Info className="h-3.5 w-3.5 cursor-help text-zinc-500 hover:text-zinc-300" />
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
                            const tabKey = key as
                              | "manual"
                              | "schedule"
                              | "trigger";
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

                  {/* Separator */}
                  <div className="border-t border-zinc-800" />

                  {/* Description Section */}
                  <div className="space-y-4">
                    <Textarea
                      placeholder={
                        mode === "edit"
                          ? "Edit workflow description"
                          : "Describe what this workflow should do when triggered"
                      }
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
                </div>

                {/* Form Footer */}
                <div className="mt-8 border-t border-zinc-800 pt-6 pb-3">
                  {/* All controls in one row */}
                  <div className="flex items-center justify-between">
                    {/* Left side: Switch and Run Workflow */}
                    <div className="flex items-center gap-4">
                      {existingWorkflow && (
                        <Tooltip
                          content="Manually run workflow"
                          placement="top"
                        >
                          <Button
                            color="success"
                            variant="flat"
                            startContent={<Play className="h-4 w-4" />}
                            onPress={handleRunWorkflow}
                            size="sm"
                          >
                            Run Manually
                          </Button>
                        </Tooltip>
                      )}

                      {mode === "edit" && (
                        <div className="flex items-center gap-3">
                          <Tooltip
                            content={
                              isActivated
                                ? "Deactivate this workflow to prevent it from running"
                                : "Activate this workflow to allow it to run"
                            }
                            placement="top"
                          >
                            <Switch
                              isSelected={isActivated}
                              onValueChange={handleActivationToggle}
                              isDisabled={isTogglingActivation}
                              size="sm"
                            />
                          </Tooltip>
                        </div>
                      )}
                    </div>

                    {/* Right side: Cancel and Save */}
                    <div className="flex items-center gap-3">
                      <Button variant="flat" onPress={handleClose}>
                        Cancel
                      </Button>
                      <Button
                        color="primary"
                        onPress={handleSave}
                        isLoading={isCreating}
                        isDisabled={
                          !formData.title.trim() ||
                          !formData.description.trim() ||
                          (formData.activeTab === "schedule" &&
                            !formData.trigger_config.cron_expression)
                        }
                      >
                        {getButtonText()}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right side - Workflow Steps */}
              {mode === "edit" && (
                <div className="flex min-h-0 w-96 flex-col space-y-4 rounded-2xl bg-zinc-950/50 p-6">
                  {/* Show regeneration error state */}
                  {regenerationError && (
                    <div className="space-y-4">
                      <div className="flex flex-col items-center justify-center py-8">
                        <div className="text-center">
                          <div className="mb-4">
                            <AlertCircle className="mx-auto h-12 w-12 text-danger" />
                          </div>
                          <h3 className="text-lg font-medium text-danger">
                            Generation Failed
                          </h3>
                          <p className="mb-4 text-sm text-zinc-400">
                            {regenerationError}
                          </p>
                          <Button
                            variant="flat"
                            size="sm"
                            onPress={() => {
                              setRegenerationError(null);
                            }}
                          >
                            Try Again
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Show workflow steps - either existing or newly generated */}
                  {existingWorkflow && !regenerationError && (
                    <>
                      {/* Show steps if they exist */}
                      {currentWorkflow?.steps &&
                      currentWorkflow.steps.length > 0 ? (
                        <>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium text-zinc-200">
                                Workflow Steps
                              </h4>
                              <Chip
                                size="sm"
                                color="primary"
                                className="text-sm font-medium"
                              >
                                {currentWorkflow.steps.length}
                              </Chip>
                            </div>
                            <div className="flex items-center gap-2">
                              <Dropdown placement="bottom-end">
                                <DropdownTrigger>
                                  <Button
                                    variant="flat"
                                    size="sm"
                                    color="primary"
                                    isLoading={isRegeneratingSteps}
                                    isDisabled={isRegeneratingSteps}
                                    endContent={
                                      !isRegeneratingSteps && (
                                        <ChevronDown className="h-3 w-3" />
                                      )
                                    }
                                    startContent={
                                      <RefreshCw className="h-4 w-4" />
                                    }
                                  >
                                    {isRegeneratingSteps
                                      ? "Regenerating..."
                                      : "Regenerate"}
                                  </Button>
                                </DropdownTrigger>
                                <DropdownMenu
                                  aria-label="Regeneration reasons"
                                  onAction={(key) =>
                                    handleRegenerateWithReason(key as string)
                                  }
                                  disabledKeys={
                                    isRegeneratingSteps ? ["all"] : []
                                  }
                                >
                                  {regenerationReasons.map((reason) => (
                                    <DropdownItem
                                      key={reason.key}
                                      description={reason.description}
                                    >
                                      {reason.label}
                                    </DropdownItem>
                                  ))}
                                </DropdownMenu>
                              </Dropdown>
                            </div>
                          </div>
                          <div className="min-h-0 flex-1 overflow-y-auto">
                            <WorkflowSteps
                              steps={currentWorkflow.steps || []}
                            />
                          </div>
                        </>
                      ) : (
                        // Show empty state with generate button (when no steps in either source)
                        <div className="space-y-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-medium text-zinc-200">
                                Workflow Steps
                              </h4>
                              <p className="text-xs text-zinc-500">
                                No steps generated yet
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                variant="flat"
                                size="sm"
                                color="primary"
                                isLoading={isRegeneratingSteps}
                                isDisabled={isRegeneratingSteps}
                                startContent={<RefreshCw className="h-4 w-4" />}
                                onPress={handleInitialGeneration}
                              >
                                Generate Steps
                              </Button>
                            </div>
                          </div>
                          <div className="flex flex-col items-center justify-center py-8 text-center">
                            <div className="mb-4 rounded-full bg-zinc-800/50 p-3">
                              <RefreshCw className="h-6 w-6 text-zinc-500" />
                            </div>
                            <p className="text-sm text-zinc-400">
                              Click "Generate Steps" to create your first
                              workflow plan
                            </p>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          ) : creationPhase === "error" ? (
            <div className="flex flex-col items-center justify-center space-y-4 py-8">
              <AlertCircle className="h-12 w-12 text-danger" />
              <div className="text-center">
                <h3 className="text-lg font-medium text-danger">
                  {mode === "create" ? "Creation" : "Update"} Failed
                </h3>
                <p className="text-sm text-zinc-400">
                  {creationError ||
                    `Something went wrong while ${mode === "create" ? "creating" : "updating"} the workflow`}
                </p>
              </div>
              <div className="flex gap-3">
                <Button variant="flat" onPress={handleClose}>
                  Cancel
                </Button>
                <Button
                  color="primary"
                  onPress={() => setCreationPhase("form")}
                >
                  Try Again
                </Button>
              </div>
            </div>
          ) : creationPhase === "generating" ? (
            <div className="flex flex-col items-center justify-center space-y-4 py-8">
              <CustomSpinner variant="logo" />
              <div className="text-center">
                <h3 className="text-lg font-medium">Generating Steps</h3>
                <p className="text-sm text-zinc-400">
                  AI is creating workflow steps for: "{formData.title}"
                </p>
                {currentWorkflow && (
                  <p className="mt-2 text-xs text-zinc-500">
                    Activated: {currentWorkflow.activated ? "Yes" : "No"}
                  </p>
                )}
              </div>
              <Button variant="flat" onPress={handleClose}>
                Close
              </Button>
            </div>
          ) : creationPhase === "creating" ? (
            <div className="flex flex-col items-center justify-center space-y-4 py-8">
              <CustomSpinner variant="simple" />
              <div className="text-center">
                <h3 className="text-lg font-medium">Creating Workflow</h3>
                <p className="text-sm text-zinc-400">
                  Setting up your workflow...
                </p>
              </div>
            </div>
          ) : creationPhase === "success" ? (
            <div className="flex flex-col space-y-6 py-6">
              <div className="flex flex-col items-center justify-center space-y-4">
                <CheckmarkCircle02Icon className="h-16 w-16 text-success" />
                <div className="text-center">
                  <h3 className="text-lg font-medium text-success">
                    Workflow {mode === "create" ? "Created" : "Updated"}!
                  </h3>
                  <p className="text-sm text-zinc-400">
                    "{formData.title}" is ready to use
                  </p>
                  {currentWorkflow && (
                    <p className="mt-2 text-xs text-zinc-500">
                      {currentWorkflow?.steps?.length || 0} steps generated
                    </p>
                  )}
                </div>
                {/* Countdown close button */}
                <Button
                  color="primary"
                  variant="flat"
                  onPress={handleClose}
                  className="mt-4"
                >
                  Close {countdown > 0 && `(${countdown}s)`}
                </Button>
              </div>

              {/* Generated Steps Preview */}
              {currentWorkflow?.steps && currentWorkflow.steps.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-zinc-300">
                    Generated Steps:
                  </h4>
                  <div className="max-h-48 overflow-y-auto">
                    <WorkflowSteps steps={currentWorkflow.steps} />
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}
