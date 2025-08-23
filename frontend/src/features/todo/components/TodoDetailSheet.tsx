"use client";

import { Button, Drawer, DrawerContent, DrawerBody } from "@heroui/react";
import { Input, Textarea } from "@heroui/input";
import { formatDistanceToNow } from "date-fns";
import { Check, Trash2 } from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";

import { useUser } from "@/features/auth/hooks/useUser";
import { todoApi } from "@/features/todo/api/todoApi";
import {
  Priority,
  Project,
  Todo,
  TodoUpdate,
  Workflow,
} from "@/types/features/todoTypes";

import SubtaskManager from "./shared/SubtaskManager";
import TodoFieldsRow from "./shared/TodoFieldsRow";
import WorkflowSection from "./WorkflowSection";

interface TodoDetailSheetProps {
  todo: Todo | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (todoId: string, updates: TodoUpdate) => void;
  onDelete: (todoId: string) => void;
  projects: Project[];
}

export default function TodoDetailSheet({
  todo,
  isOpen,
  onClose,
  onUpdate,
  onDelete,
  projects,
}: TodoDetailSheetProps) {
  const user = useUser();
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [isGeneratingWorkflow, setIsGeneratingWorkflow] = useState(false);

  const userTimezone = user?.onboarding?.preferences?.timezone;

  if (!todo) return null;

  const handleToggleComplete = () => {
    try {
      onUpdate(todo.id, { completed: !todo.completed });
    } catch (error) {
      console.error("Failed to update todo:", error);
    }
  };

  const handleDelete = () => {
    onDelete(todo.id);
    onClose();
  };

  const handleSubtasksChange = (subtasks: typeof todo.subtasks) => {
    onUpdate(todo.id, { subtasks });
  };

  const handleTitleSave = (newTitle: string) => {
    if (newTitle.trim() && newTitle !== todo.title) {
      onUpdate(todo.id, { title: newTitle.trim() });
    }
    setIsEditingTitle(false);
  };

  const handleDescriptionSave = (newDescription: string) => {
    if (newDescription !== todo.description) {
      onUpdate(todo.id, { description: newDescription });
    }
    setIsEditingDescription(false);
  };

  const handleFieldChange = (
    field: keyof TodoUpdate,
    value: string | string[] | Priority | undefined,
  ) => {
    onUpdate(todo.id, { [field]: value } as TodoUpdate);
  };

  const handleGenerateWorkflow = async () => {
    setIsGeneratingWorkflow(true);
    try {
      const updatedTodo = await todoApi.generateWorkflow(todo.id);
      if (updatedTodo.workflow) {
        onUpdate(todo.id, updatedTodo);
        toast.success("Workflow generated successfully!");
      }
    } catch (error) {
      console.error("Failed to generate workflow:", error);
      toast.error("Failed to generate workflow");
    } finally {
      setIsGeneratingWorkflow(false);
    }
  };

  const handleWorkflowGenerated = (workflow: Workflow) => {
    onUpdate(todo.id, { workflow });
    toast.success("Workflow generated successfully!");
  };

  return (
    <Drawer
      isOpen={isOpen}
      onOpenChange={(open) => !open && onClose()}
      placement="right"
      size="lg"
    >
      <DrawerContent>
        {(onClose) => (
          <DrawerBody className="w-[500px] max-w-[90vw] overflow-hidden bg-zinc-900 p-0">
            <div className="flex h-full flex-col">
              <div className="flex-1 overflow-y-auto">
                {/* Title and Description Section */}
                <div className="px-6 py-6 pt-8">
                  <div className="flex items-start gap-4">
                    <button
                      onClick={handleToggleComplete}
                      className={`mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full transition-all duration-200 ${
                        todo.completed
                          ? "bg-green-500"
                          : "border border-zinc-500 hover:border-zinc-400 hover:bg-zinc-800"
                      }`}
                    >
                      {todo.completed && (
                        <Check className="h-3 w-3 text-white" />
                      )}
                    </button>
                    <div className="flex-1 space-y-3">
                      {/* Editable Title with Delete Button */}
                      {isEditingTitle ? (
                        <div className="flex items-center justify-between">
                          <Input
                            defaultValue={todo.title}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleTitleSave(e.currentTarget.value);
                              }
                              if (e.key === "Escape") {
                                setIsEditingTitle(false);
                              }
                            }}
                            onBlur={(e) => handleTitleSave(e.target.value)}
                            autoFocus
                            classNames={{
                              input:
                                "text-2xl font-medium bg-transparent border-0 text-zinc-100 placeholder:text-zinc-500",
                              inputWrapper:
                                "border-0 bg-transparent shadow-none hover:bg-transparent focus:bg-transparent data-[focus=true]:bg-transparent",
                            }}
                            variant="underlined"
                            className="mr-4 flex-1"
                          />
                          <Button
                            size="sm"
                            variant="light"
                            isIconOnly
                            color="danger"
                            onPress={handleDelete}
                            className="h-8 w-8 flex-shrink-0 text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between">
                          <h1
                            onClick={() => setIsEditingTitle(true)}
                            className={`mr-4 flex-1 cursor-pointer text-2xl leading-tight font-medium transition-colors hover:text-zinc-200 ${
                              todo.completed
                                ? "text-zinc-500 line-through"
                                : "text-zinc-100"
                            }`}
                          >
                            {todo.title}
                          </h1>
                          <Button
                            size="sm"
                            variant="light"
                            isIconOnly
                            color="danger"
                            onPress={handleDelete}
                            className="h-8 w-8 flex-shrink-0 text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      )}

                      {/* Editable Description */}
                      {isEditingDescription ? (
                        <Textarea
                          defaultValue={todo.description || ""}
                          onKeyDown={(e) => {
                            if (e.key === "Escape") {
                              setIsEditingDescription(false);
                            }
                          }}
                          onBlur={(e) => handleDescriptionSave(e.target.value)}
                          placeholder="Add a description..."
                          minRows={2}
                          maxRows={4}
                          autoFocus
                          classNames={{
                            input:
                              "bg-transparent border-0 text-zinc-200 placeholder:text-zinc-500",
                            inputWrapper:
                              "border-0 bg-transparent shadow-none hover:bg-transparent focus:bg-transparent data-[focus=true]:bg-transparent",
                          }}
                          variant="underlined"
                        />
                      ) : (
                        <p
                          onClick={() => setIsEditingDescription(true)}
                          className={`cursor-pointer text-sm leading-relaxed transition-colors hover:text-zinc-300 ${
                            todo.completed ? "text-zinc-600" : "text-zinc-400"
                          }`}
                        >
                          {todo.description || "Add a description..."}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Editable Fields */}
                <div className="px-6 py-4">
                  <TodoFieldsRow
                    priority={todo.priority}
                    projectId={todo.project_id}
                    projects={projects}
                    dueDate={todo.due_date}
                    dueDateTimezone={todo.due_date_timezone}
                    labels={todo.labels}
                    onPriorityChange={(priority) =>
                      handleFieldChange("priority", priority)
                    }
                    onProjectChange={(projectId) =>
                      handleFieldChange("project_id", projectId)
                    }
                    onDateChange={(date, timezone) => {
                      handleFieldChange("due_date", date);
                      if (timezone)
                        handleFieldChange("due_date_timezone", timezone);
                    }}
                    onLabelsChange={(labels) =>
                      handleFieldChange("labels", labels)
                    }
                    userTimezone={userTimezone}
                  />
                </div>

                {/* Created Info */}
                <div className="px-6 py-2">
                  <span className="text-xs text-zinc-500">
                    Created{" "}
                    {formatDistanceToNow(new Date(todo.created_at), {
                      addSuffix: true,
                    })}
                  </span>
                </div>

                {/* Subtasks Section */}
                <div className="px-6 py-4 pt-6">
                  <SubtaskManager
                    subtasks={todo.subtasks}
                    onSubtasksChange={handleSubtasksChange}
                  />
                </div>

                {/* Workflow Section */}
                <div className="px-6 py-4 pt-6">
                  <WorkflowSection
                    workflow={todo.workflow}
                    isGenerating={isGeneratingWorkflow}
                    workflowStatus={todo.workflow_status}
                    todoId={todo.id}
                    todoTitle={todo.title}
                    todoDescription={todo.description}
                    onGenerateWorkflow={handleGenerateWorkflow}
                    onWorkflowGenerated={handleWorkflowGenerated}
                  />
                </div>
              </div>
            </div>
          </DrawerBody>
        )}
      </DrawerContent>
    </Drawer>
  );
}
