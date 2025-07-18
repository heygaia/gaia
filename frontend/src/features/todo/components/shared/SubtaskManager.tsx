"use client";

import { Checkbox } from "@heroui/checkbox";
import { Plus, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/shadcn/button";
import { Input } from "@/components/ui/shadcn/input";
import { cn } from "@/lib/utils";
import { SubTask } from "@/types/features/todoTypes";

interface SubtaskManagerProps {
  subtasks: SubTask[];
  onSubtasksChange: (subtasks: SubTask[]) => void;
  className?: string;
}

export default function SubtaskManager({
  subtasks,
  onSubtasksChange,
  className,
}: SubtaskManagerProps) {
  const [newSubtaskTitle, setNewSubtaskTitle] = useState("");
  const [editingSubtaskId, setEditingSubtaskId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  const handleAddSubtask = () => {
    if (!newSubtaskTitle.trim()) return;

    const newSubtask: SubTask = {
      id: Date.now().toString(),
      title: newSubtaskTitle.trim(),
      completed: false,
      created_at: new Date().toISOString(),
    };

    onSubtasksChange([...subtasks, newSubtask]);
    setNewSubtaskTitle("");
  };

  const handleToggleSubtask = (subtaskId: string) => {
    const updatedSubtasks = subtasks.map((subtask) =>
      subtask.id === subtaskId
        ? { ...subtask, completed: !subtask.completed }
        : subtask,
    );
    onSubtasksChange(updatedSubtasks);
  };

  const handleDeleteSubtask = (subtaskId: string) => {
    const updatedSubtasks = subtasks.filter(
      (subtask) => subtask.id !== subtaskId,
    );
    onSubtasksChange(updatedSubtasks);
  };

  const handleStartEdit = (subtask: SubTask) => {
    setEditingSubtaskId(subtask.id);
    setEditingTitle(subtask.title);
  };

  const handleSaveEdit = () => {
    if (!editingTitle.trim() || !editingSubtaskId) return;

    const updatedSubtasks = subtasks.map((subtask) =>
      subtask.id === editingSubtaskId
        ? { ...subtask, title: editingTitle.trim() }
        : subtask,
    );
    onSubtasksChange(updatedSubtasks);
    setEditingSubtaskId(null);
    setEditingTitle("");
  };

  const handleCancelEdit = () => {
    setEditingSubtaskId(null);
    setEditingTitle("");
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    action: "add" | "edit",
  ) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (action === "add") {
        handleAddSubtask();
      } else {
        handleSaveEdit();
      }
    } else if (e.key === "Escape" && action === "edit") {
      handleCancelEdit();
    }
  };

  return (
    <div className={cn("space-y-3", className)}>
      {/* Subtasks Header */}
      {subtasks.length > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-zinc-300">
            Subtasks ({subtasks.filter((s) => s.completed).length}/
            {subtasks.length})
          </span>
        </div>
      )}

      {/* Add New Subtask */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            placeholder="Add a subtask..."
            value={newSubtaskTitle}
            onChange={(e) => setNewSubtaskTitle(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, "add")}
            className="hover:bg-zinc-750 h-9 rounded-lg border-0 bg-zinc-800 text-sm text-zinc-200 placeholder:text-zinc-500 focus:ring-0 focus:outline-none"
          />
        </div>
        <Button
          size="sm"
          onClick={handleAddSubtask}
          disabled={!newSubtaskTitle.trim()}
          className={`h-9 w-9 rounded-lg border-0 p-0 ${
            !newSubtaskTitle.trim()
              ? "hover:bg-zinc-750 bg-zinc-800 text-zinc-600"
              : "hover:bg-zinc-750 bg-zinc-800 text-zinc-200"
          }`}
        >
          <Plus size={16} />
        </Button>
      </div>

      {/* Existing Subtasks */}
      {subtasks.length > 0 && (
        <div className="space-y-2">
          {subtasks.map((subtask) => (
            <div
              key={subtask.id}
              className="group hover:bg-zinc-750 flex items-center gap-3 rounded-lg bg-zinc-800 p-2 transition-colors"
            >
              <Checkbox
                isSelected={subtask.completed}
                onChange={() => handleToggleSubtask(subtask.id)}
                radius="full"
                size="sm"
                color="success"
                className="flex-shrink-0"
              />

              {editingSubtaskId === subtask.id ? (
                <div className="flex flex-1 gap-2">
                  <Input
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onKeyDown={(e) => handleKeyDown(e, "edit")}
                    className="bg-zinc-750 h-7 flex-1 rounded-md border-0 text-sm text-zinc-200 focus:ring-0 focus:outline-none"
                    autoFocus
                  />
                  <Button
                    size="sm"
                    onClick={handleSaveEdit}
                    disabled={!editingTitle.trim()}
                    className="bg-zinc-750 h-7 w-7 rounded-md border-0 p-0 text-xs text-zinc-200 hover:bg-zinc-600"
                  >
                    ✓
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleCancelEdit}
                    className="h-7 w-7 rounded-md border-0 p-0 text-zinc-400 hover:bg-zinc-600 hover:text-zinc-200"
                  >
                    <X size={12} />
                  </Button>
                </div>
              ) : (
                <>
                  <span
                    className={cn(
                      "flex-1 cursor-pointer text-sm text-zinc-200 select-none",
                      subtask.completed && "text-zinc-500 line-through",
                    )}
                    onClick={() => handleStartEdit(subtask)}
                  >
                    {subtask.title}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDeleteSubtask(subtask.id)}
                    className="h-7 w-7 rounded-md border-0 p-0 text-zinc-500 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-zinc-600 hover:text-red-400"
                  >
                    <X size={14} />
                  </Button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
