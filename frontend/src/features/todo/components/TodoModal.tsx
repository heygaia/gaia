"use client";

import { Button } from "@heroui/button";
import { Input, Textarea } from "@heroui/input";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@heroui/modal";
import { useEffect, useMemo } from "react";

import { todoApi } from "@/features/todo/api/todoApi";
import { useModalForm } from "@/hooks/ui/useModalForm";
import {
  Priority,
  Project,
  Todo,
  TodoCreate,
} from "@/types/features/todoTypes";

import SubtaskManager from "./shared/SubtaskManager";
import TodoFieldsRow from "./shared/TodoFieldsRow";

interface TodoModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
  mode: "add" | "edit";
  todo?: Todo; // Required when mode is "edit"
  initialProjectId?: string; // Used when mode is "add"
  projects: Project[]; // Pass projects as props instead of using Redux
}

function getChangedFields<T extends object>(
  original: T,
  updated: T,
): Partial<T> {
  const changes: Partial<T> = {};

  for (const key in updated) {
    const originalValue = original[key];
    const updatedValue = updated[key];

    const isEqual =
      typeof originalValue === "object"
        ? JSON.stringify(originalValue) === JSON.stringify(updatedValue)
        : originalValue === updatedValue;

    if (!isEqual) {
      changes[key] = updatedValue;
    }
  }

  return changes;
}

export default function TodoModal({
  open,
  onOpenChange,
  onSuccess,
  mode,
  todo,
  initialProjectId,
  projects,
}: TodoModalProps) {
  const initialData = useMemo(() => {
    if (mode === "edit" && todo) {
      return {
        title: todo.title,
        description: todo.description,
        labels: todo.labels,
        priority: todo.priority,
        project_id: todo.project_id,
        due_date: todo.due_date,
        due_date_timezone: todo.due_date_timezone,
        subtasks: todo.subtasks || [],
      };
    }

    return {
      title: "",
      description: "",
      labels: [],
      priority: Priority.NONE,
      project_id: initialProjectId,
      subtasks: [],
    };
  }, [mode, todo?.id, initialProjectId]);

  const { formData, setFormData, loading, handleSubmit, updateField } =
    useModalForm<TodoCreate>({
      initialData,
      onSubmit: async (data: TodoCreate) => {
        if (mode === "edit" && todo) {
          const updates = getChangedFields(todo, data);

          if (Object.keys(updates).length > 0) {
            await todoApi.updateTodo(todo.id, updates);
          }
          return;
        }

        await todoApi.createTodo(data);
      },
      validate: [
        {
          field: "title",
          required: true,
          message: "Please enter a task title",
        },
      ],
      onSuccess: () => {
        onOpenChange(false);
        onSuccess?.();
      },
      resetOnSuccess: mode === "add",
    });

  // Set initial project ID when it changes (add mode)
  useEffect(() => {
    if (mode === "add" && initialProjectId) {
      updateField("project_id", initialProjectId);
    }
  }, [mode, initialProjectId, updateField]);

  // Set default project when modal opens in add mode
  useEffect(() => {
    if (open && mode === "add" && projects.length > 0 && !formData.project_id) {
      const inboxProject = projects.find((p: Project) => p.is_default);
      if (inboxProject) {
        updateField("project_id", inboxProject.id);
      }
    }
  }, [open, mode, projects.length, updateField]); // Only run when modal opens

  // Reset form data when modal opens with todo (edit mode)
  useEffect(() => {
    if (open && mode === "edit" && todo) {
      setFormData({
        title: todo.title,
        description: todo.description,
        labels: todo.labels,
        priority: todo.priority,
        project_id: todo.project_id,
        due_date: todo.due_date,
        due_date_timezone: todo.due_date_timezone,
        subtasks: todo.subtasks || [],
      });
    }
  }, [open, mode, todo, setFormData]);

  const handleDateChange = (date?: string, timezone?: string) => {
    setFormData((prev) => ({
      ...prev,
      due_date: date,
      due_date_timezone: timezone,
    }));
  };

  return (
    <Modal isOpen={open} onOpenChange={onOpenChange} size="lg">
      <ModalContent>
        <>
          <ModalHeader className="flex flex-col gap-1">
            {mode === "edit" ? "Edit Task" : "Add Task"}
          </ModalHeader>
          <ModalBody className="gap-6">
            <div className="flex flex-col">
              {/* Title */}
              <Input
                placeholder="Task title"
                classNames={{
                  input:
                    "text-2xl font-semibold bg-transparent border-0 text-zinc-100 placeholder:text-zinc-500",
                  inputWrapper:
                    "border-0 bg-transparent shadow-none hover:bg-transparent focus:bg-transparent data-[focus=true]:bg-transparent",
                }}
                value={formData.title}
                variant="underlined"
                onChange={(e) => updateField("title", e.target.value)}
                required
                autoFocus
              />

              {/* Description */}
              <Textarea
                placeholder="Add a description..."
                value={formData.description || ""}
                onChange={(e) => updateField("description", e.target.value)}
                minRows={1}
                maxRows={5}
                variant="underlined"
                classNames={{
                  input:
                    "bg-transparent border-0 text-zinc-200 placeholder:text-zinc-500",
                  inputWrapper:
                    "border-0 bg-transparent shadow-none hover:bg-transparent focus:bg-transparent data-[focus=true]:bg-transparent",
                }}
              />
            </div>

            {/* Fields Row with Chips */}
            <TodoFieldsRow
              priority={formData.priority}
              projectId={formData.project_id}
              projects={projects}
              dueDate={formData.due_date}
              dueDateTimezone={formData.due_date_timezone}
              labels={formData.labels}
              onPriorityChange={(priority) => updateField("priority", priority)}
              onProjectChange={(projectId) =>
                updateField("project_id", projectId)
              }
              onDateChange={handleDateChange}
              onLabelsChange={(labels) => updateField("labels", labels)}
            />

            {/* Subtasks Manager */}
            <SubtaskManager
              subtasks={formData.subtasks || []}
              onSubtasksChange={(subtasks) => updateField("subtasks", subtasks)}
            />
          </ModalBody>

          <ModalFooter>
            <Button variant="light" onPress={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              color="primary"
              onPress={handleSubmit}
              isDisabled={loading}
              isLoading={loading}
            >
              {mode === "edit" ? "Save Changes" : "Add Task"}
            </Button>
          </ModalFooter>
        </>
      </ModalContent>
    </Modal>
  );
}
