"use client";

import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Input } from "@heroui/input";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  useDisclosure,
} from "@heroui/modal";
import { Select, SelectItem } from "@heroui/select";
import { Tab, Tabs } from "@heroui/tabs";
import { Tooltip } from "@heroui/tooltip";
import { Textarea } from "@heroui/input";
import { Calendar, Clock, Info } from "lucide-react";
import Image from "next/image";
import React, { useState } from "react";

import {
  dayOptions,
  integrationOptions,
  intervalOptions,
  monthOptions,
  scheduleFrequencyOptions,
  triggerOptions,
  TriggerOption,
  IntegrationOption,
} from "../data/workflowData";

interface WorkflowFormData {
  name: string;
  description: string;
  activeTab: "trigger" | "schedule";
  trigger: string;
  integrations: string[];
  schedule: {
    frequency: string;
    interval: string;
    selectedDay: string;
    selectedMonth: string;
    time: string;
    date: string;
  };
}

interface CreateWorkflowModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function CreateWorkflowModal({
  isOpen,
  onOpenChange,
}: CreateWorkflowModalProps) {
  const [formData, setFormData] = useState<WorkflowFormData>({
    name: "Untitled Workflow",
    description: "",
    activeTab: "trigger",
    trigger: "",
    integrations: [],
    schedule: {
      frequency: "every",
      interval: "day",
      selectedDay: "",
      selectedMonth: "",
      time: "",
      date: "",
    },
  });

  const selectedTriggerOption = triggerOptions.find(
    (t) => t.id === formData.trigger,
  );
  const selectedIntegrationOptions = integrationOptions.filter((i) =>
    formData.integrations.includes(i.id),
  );

  const updateFormData = (updates: Partial<WorkflowFormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  const updateScheduleData = (
    updates: Partial<WorkflowFormData["schedule"]>,
  ) => {
    setFormData((prev) => ({
      ...prev,
      schedule: { ...prev.schedule, ...updates },
    }));
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      activeTab: "trigger",
      trigger: "",
      integrations: [],
      schedule: {
        frequency: "every",
        interval: "day",
        selectedDay: "",
        selectedMonth: "",
        time: "",
        date: "",
      },
    });
  };

  const handleCreate = () => {
    // Handle workflow creation here
    console.log("Creating workflow:", formData);
    resetForm();
    onOpenChange(false);
  };

  const handleClose = () => {
    resetForm();
    onOpenChange(false);
  };

  const renderTriggerTab = () => (
    <div className="space-y-2">
      <div>
        <Select
          fullWidth
          placeholder="Choose a trigger for your workflow"
          classNames={{
            innerWrapper: "min-w-fit pr-7",
            listboxWrapper: "min-w-fit!",
            base: "min-w-fit",
          }}
          selectedKeys={formData.trigger ? [formData.trigger] : []}
          onSelectionChange={(keys) =>
            updateFormData({ trigger: Array.from(keys)[0] as string })
          }
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
        <p className="px-1 text-xs text-foreground-400">
          {selectedTriggerOption.description}
        </p>
      )}
    </div>
  );

  const renderScheduleTab = () => (
    <div className="flex h-full items-center space-y-6 px-3">
      <div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span>Run</span>

          <Select
            size="sm"
            placeholder="Select frequency"
            selectedKeys={
              formData.schedule.frequency ? [formData.schedule.frequency] : []
            }
            onSelectionChange={(keys) =>
              updateScheduleData({ frequency: Array.from(keys)[0] as string })
            }
            className="w-24"
          >
            {scheduleFrequencyOptions.map((option) => (
              <SelectItem key={option.key}>{option.label}</SelectItem>
            ))}
          </Select>

          {formData.schedule.frequency === "every" && (
            <>
              <Select
                size="sm"
                placeholder="Select interval"
                selectedKeys={
                  formData.schedule.interval ? [formData.schedule.interval] : []
                }
                onSelectionChange={(keys) =>
                  updateScheduleData({
                    interval: Array.from(keys)[0] as string,
                  })
                }
                className="w-24"
              >
                {intervalOptions.map((option) => (
                  <SelectItem key={option.key}>{option.label}</SelectItem>
                ))}
              </Select>

              {formData.schedule.interval === "week" && (
                <>
                  <span>on</span>
                  <Select
                    size="sm"
                    placeholder="Select day"
                    selectedKeys={
                      formData.schedule.selectedDay
                        ? [formData.schedule.selectedDay]
                        : []
                    }
                    onSelectionChange={(keys) =>
                      updateScheduleData({
                        selectedDay: Array.from(keys)[0] as string,
                      })
                    }
                    className="w-32"
                  >
                    {dayOptions.map((option) => (
                      <SelectItem key={option.key}>{option.label}</SelectItem>
                    ))}
                  </Select>
                </>
              )}

              {formData.schedule.interval === "month" && (
                <>
                  <span>on the</span>
                  <Select
                    size="sm"
                    placeholder="Select day"
                    selectedKeys={
                      formData.schedule.selectedMonth
                        ? [formData.schedule.selectedMonth]
                        : []
                    }
                    onSelectionChange={(keys) =>
                      updateScheduleData({
                        selectedMonth: Array.from(keys)[0] as string,
                      })
                    }
                    className="w-20"
                  >
                    {monthOptions.map((option) => (
                      <SelectItem key={option.key}>{option.label}</SelectItem>
                    ))}
                  </Select>
                </>
              )}

              <span>at</span>
              <Input
                size="sm"
                type="time"
                value={formData.schedule.time}
                onChange={(e) => updateScheduleData({ time: e.target.value })}
                className="w-32"
                startContent={<Clock className="h-4 w-4 text-foreground-400" />}
              />
            </>
          )}

          {formData.schedule.frequency === "once" && (
            <>
              <span>on</span>
              <Input
                size="sm"
                type="date"
                value={formData.schedule.date}
                onChange={(e) => updateScheduleData({ date: e.target.value })}
                className="w-40"
                startContent={
                  <Calendar className="h-4 w-4 text-foreground-400" />
                }
              />
              <span>at</span>
              <Input
                size="sm"
                type="time"
                value={formData.schedule.time}
                onChange={(e) => updateScheduleData({ time: e.target.value })}
                className="w-32"
                startContent={<Clock className="h-4 w-4 text-foreground-400" />}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) resetForm();
        onOpenChange(open);
      }}
      size="5xl"
      className="min-h-[50vh]"
      scrollBehavior="inside"
      backdrop="blur"
    >
      <ModalContent>
        <ModalBody className="space-y-6 pt-8">
          {/* Basic Information */}
          <div className="space-y-1">
            <Input
              placeholder="Enter workflow name"
              value={formData.name}
              variant="underlined"
              //   className="text-3xl! font-medium"
              classNames={{
                input: "font-semibold! text-4xl",
                inputWrapper: "px-0",
              }}
              onChange={(e) => updateFormData({ name: e.target.value })}
              isRequired
            />

            <Textarea
              placeholder="Describe what this workflow does"
              value={formData.description}
              onChange={(e) => updateFormData({ description: e.target.value })}
              maxRows={10}
              minRows={10}
              variant="underlined"
              className="text-sm"
            />
          </div>

          <div className="space-y-3">
            {/* Trigger/Schedule Tabs. rounded-2xl bg-zinc-800/50 p-1 pb-0 */}

            <div className="flex items-center gap-3">
              <div className="flex min-w-28 items-center justify-between gap-1.5 text-sm font-medium text-foreground-500">
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
                          • <span className="font-medium">Trigger:</span> Run
                          when specific events occur (new emails, messages,
                          etc.)
                        </li>
                        <li>
                          • <span className="font-medium">Schedule:</span> Run
                          at specific times or intervals
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
                    tabList: "flex flex-row max-w-md",
                    base: "flex items-start",
                  }}
                  selectedKey={formData.activeTab}
                  //   variant="bordered"
                  placement="start"
                  onSelectionChange={(key) =>
                    updateFormData({ activeTab: key as "trigger" | "schedule" })
                  }
                >
                  <Tab key="trigger" title="Trigger">
                    {renderTriggerTab()}
                  </Tab>
                  <Tab key="schedule" title="Schedule">
                    {renderScheduleTab()}
                  </Tab>
                </Tabs>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex min-w-28 items-center justify-between gap-1.5 text-sm font-medium text-foreground-500">
                <span>Integrations</span>
                <Tooltip
                  content={
                    <div className="px-1 py-2">
                      <p className="text-sm font-medium">Integrations</p>
                      <p className="mt-1 text-xs text-foreground-400">
                        Select which tools and services GAIA will interact with
                        in this workflow.
                      </p>
                      <ul className="mt-2 space-y-1 text-xs text-foreground-400">
                        <li>• Connect to your favorite productivity apps</li>
                        <li>• Automate tasks across multiple platforms</li>
                        <li>
                          • Each integration provides specific capabilities
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

              <Select
                placeholder="Choose integrations GAIA will use in this workflow"
                selectionMode="multiple"
                className="max-w-md"
                selectedKeys={formData.integrations}
                onSelectionChange={(keys) =>
                  updateFormData({ integrations: Array.from(keys) as string[] })
                }
                renderValue={(items) => (
                  <div className="flex flex-wrap gap-2">
                    {items.map((item) => {
                      const integration = integrationOptions.find(i => i.id === item.key);
                      return integration ? (
                        <Chip
                          key={item.key}
                          size="sm"
                          variant="flat"
                          startContent={
                            <Image
                              src={integration.icon}
                              alt={integration.name}
                              width={16}
                              height={16}
                              className="h-4 w-4 object-contain"
                            />
                          }
                        >
                          {integration.name}
                        </Chip>
                      ) : null;
                    })}
                  </div>
                )}
              >
                {integrationOptions.map((integration) => (
                  <SelectItem
                    key={integration.id}
                    startContent={
                      <Image
                        src={integration.icon}
                        alt={integration.name}
                        width={20}
                        height={20}
                        className="h-5 w-5 object-contain"
                      />
                    }
                    endContent={
                      <Chip size="sm" variant="flat" className="capitalize">
                        {integration.category}
                      </Chip>
                    }
                  >
                    {integration.name}
                  </SelectItem>
                ))}
              </Select>
            </div>
          </div>
        </ModalBody>

        <ModalFooter>
          <Button variant="flat" onPress={handleClose}>
            Cancel
          </Button>
          <Button
            color="primary"
            onPress={handleCreate}
            isDisabled={
              !formData.name ||
              formData.integrations.length === 0 ||
              (formData.activeTab === "trigger" && !formData.trigger)
            }
          >
            Create Workflow
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
