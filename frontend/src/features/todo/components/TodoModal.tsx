"use client";

import { Input, Textarea } from "@heroui/input";
import { useEffect } from "react";

import { Button } from "@/components/ui/shadcn/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
} from "@/components/ui/shadcn/dialog";
import { useTodos } from "@/features/todo/hooks/useTodos";
import { useModalForm } from "@/hooks/ui/useModalForm";
import {
  Priority,
  Todo,
  TodoCreate,
  TodoUpdate,
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
}

export default function TodoModal({
  open,
  onOpenChange,
  onSuccess,
  mode,
  todo,
  initialProjectId,
}: TodoModalProps) {
  const { projects, addTodo, modifyTodo } = useTodos();

  const getInitialData = (): TodoCreate => {
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
  };

  const { formData, setFormData, loading, handleSubmit, updateField } =
    useModalForm<TodoCreate>({
      initialData: getInitialData,
      onSubmit: async (data: TodoCreate) => {
        if (mode === "edit" && todo) {
          // Only send changed fields for edit
          const updates: TodoUpdate = {};
          if (data.title !== todo.title) updates.title = data.title;
          if (data.description !== todo.description)
            updates.description = data.description;
          if (JSON.stringify(data.labels) !== JSON.stringify(todo.labels))
            updates.labels = data.labels;
          if (data.priority !== todo.priority) updates.priority = data.priority;
          if (data.project_id !== todo.project_id)
            updates.project_id = data.project_id;
          if (data.due_date !== todo.due_date) {
            updates.due_date = data.due_date;
            updates.due_date_timezone = data.due_date_timezone;
          }
          if (JSON.stringify(data.subtasks) !== JSON.stringify(todo.subtasks)) {
            updates.subtasks = data.subtasks;
          }

          if (Object.keys(updates).length > 0) {
            await modifyTodo(todo.id, updates);
          }
        } else {
          await addTodo(data);
        }
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

  // Set default project when projects are loaded (add mode)
  useEffect(() => {
    if (mode === "add" && !formData.project_id && projects.length > 0) {
      const inboxProject = projects.find((p) => p.is_default);
      if (inboxProject) {
        updateField("project_id", inboxProject.id);
      }
    }
  }, [mode, projects, formData.project_id, updateField]);

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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl rounded-2xl border-none bg-zinc-900">
        <div className="flex flex-col gap-6">
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
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-0 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-zinc-200"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="border-0 bg-zinc-800 text-zinc-200 hover:bg-zinc-700 disabled:bg-zinc-800 disabled:text-zinc-500"
          >
            {loading
              ? mode === "edit"
                ? "Saving..."
                : "Adding..."
              : mode === "edit"
                ? "Save Changes"
                : "Add Task"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
