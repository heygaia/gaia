"use client";

import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import Spinner from "@/components/ui/shadcn/spinner";
import TodoDetailSheet from "@/features/todo/components/TodoDetailSheet";
import TodoHeader from "@/features/todo/components/TodoHeader";
import TodoList from "@/features/todo/components/TodoList";
import { useTodoData } from "@/features/todo/hooks/useTodoData";
import { useUrlTodoSelection } from "@/features/todo/hooks/useUrlTodoSelection";
import {
  Priority,
  Todo,
  TodoFilters,
  TodoUpdate,
} from "@/types/features/todoTypes";

export default function TodosPage() {
  const searchParams = useSearchParams();
  const { selectedTodoId, selectTodo, clearSelection } = useUrlTodoSelection();

  // Get filter from URL params
  const projectId = searchParams.get("project");
  const priority = searchParams.get("priority");
  const completedParam = searchParams.get("completed");
  const completed = completedParam === "true";

  // Helper function to validate priority value
  const getPriorityFilter = (
    priorityString: string | null,
  ): Priority | undefined => {
    if (!priorityString) return undefined;
    return Object.values(Priority).includes(priorityString as Priority)
      ? (priorityString as Priority)
      : undefined;
  };

  // Build filters from URL params
  const filters = useMemo((): TodoFilters => {
    const urlFilters: TodoFilters = {};

    // Only add filters if they are explicitly specified in URL
    if (projectId) {
      urlFilters.project_id = projectId;
    }

    if (priority) {
      const priorityValue = getPriorityFilter(priority);
      if (priorityValue) {
        urlFilters.priority = priorityValue;
      }
    }

    // Handle completed filter only if explicitly set
    if (completedParam !== null) {
      urlFilters.completed = completed;
    }

    return urlFilters;
  }, [projectId, priority, completed, completedParam]);

  const { todos, projects, loading, updateTodo, deleteTodo, refresh } =
    useTodoData({ filters, autoLoad: true });

  const handleTodoUpdate = async (todoId: string, updates: TodoUpdate) => {
    await updateTodo(todoId, updates);
  };

  const handleTodoDelete = async (todoId: string) => {
    await deleteTodo(todoId);
    // If the deleted todo was selected (shown in URL), close the detail sheet
    if (selectedTodoId === todoId) {
      clearSelection();
    }
  };

  const handleTodoEdit = (todo: Todo) => {
    selectTodo(todo.id);
  };

  if (loading && todos.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const incompleteTodos = todos.filter((t: Todo) => !t.completed);

  return (
    <div className="flex h-full w-full flex-col">
      <div className="w-full px-4">
        <TodoHeader title={getPageTitle()} todoCount={incompleteTodos.length} />
      </div>

      <div className="w-full flex-1 overflow-y-auto px-4">
        <TodoList
          todos={todos}
          onTodoUpdate={handleTodoUpdate}
          onTodoDelete={handleTodoDelete}
          onTodoEdit={handleTodoEdit}
          onTodoClick={(todo) => selectTodo(todo.id)}
          onRefresh={refresh}
        />
      </div>

      {/* Todo Detail Sheet */}
      <TodoDetailSheet
        todo={
          selectedTodoId
            ? todos.find((t: Todo) => t.id === selectedTodoId) || null
            : null
        }
        isOpen={!!selectedTodoId}
        onClose={clearSelection}
        onUpdate={handleTodoUpdate}
        onDelete={handleTodoDelete}
        projects={projects}
      />
    </div>
  );

  function getPageTitle() {
    if (projectId) return "Project Tasks";
    if (priority)
      return `${priority.charAt(0).toUpperCase() + priority.slice(1)} Priority`;
    if (completed) return "Completed Tasks";
    return "Inbox";
  }
}
