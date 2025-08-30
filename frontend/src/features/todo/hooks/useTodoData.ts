"use client";

import { useCallback, useEffect, useMemo } from "react";

import { useTodoStore } from "@/stores/todoStore";
import { Priority, TodoFilters } from "@/types/features/todoTypes";

interface UseTodoDataOptions {
  filters?: TodoFilters;
  autoLoad?: boolean;
}

export function useTodoData(options: UseTodoDataOptions = {}) {
  const { filters, autoLoad = true } = options;
  const {
    todos: allTodos,
    projects,
    labels,
    counts,
    loading,
    error,
    loadTodos,
    createTodo,
    updateTodo,
    deleteTodo,
    loadProjects,
    loadLabels,
    loadCounts,
    refreshAll,
  } = useTodoStore();

  // Filter todos based on provided filters
  const todos = useMemo(() => {
    if (!filters) return allTodos;

    return allTodos.filter((todo) => {
      // Apply completion filter
      if (
        filters.completed !== undefined &&
        todo.completed !== filters.completed
      ) {
        return false;
      }

      // Apply project filter
      if (filters.project_id && todo.project_id !== filters.project_id) {
        return false;
      }

      // Apply priority filter
      if (filters.priority && todo.priority !== filters.priority) {
        return false;
      }

      // Apply due today filter
      if (filters.due_today) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        if (!todo.due_date) return false;
        const dueDate = new Date(todo.due_date);
        return dueDate >= today && dueDate < tomorrow;
      }

      // Apply due this week filter
      if (filters.due_this_week) {
        const today = new Date();
        const nextWeek = new Date(today);
        nextWeek.setDate(nextWeek.getDate() + 7);

        if (!todo.due_date) return false;
        const dueDate = new Date(todo.due_date);
        return dueDate >= today && dueDate <= nextWeek;
      }

      return true;
    });
  }, [allTodos, filters]);

  // Load data on mount if autoLoad is enabled
  useEffect(() => {
    if (autoLoad) {
      loadTodos(filters);
    }
  }, [autoLoad, filters, loadTodos]);

  // Refresh function that reloads current filter
  const refresh = useCallback(() => {
    return loadTodos(filters);
  }, [loadTodos, filters]);

  // Convenience methods for specific todo types
  const loadTodayTodos = useCallback(() => {
    return loadTodos({ due_today: true, completed: false });
  }, [loadTodos]);

  const loadUpcomingTodos = useCallback(() => {
    return loadTodos({ due_this_week: true, completed: false });
  }, [loadTodos]);

  const loadCompletedTodos = useCallback(() => {
    return loadTodos({ completed: true });
  }, [loadTodos]);

  const loadTodosByPriority = useCallback(
    (priority: Priority) => {
      return loadTodos({ priority, completed: false });
    },
    [loadTodos],
  );

  const loadTodosByProject = useCallback(
    (projectId: string) => {
      return loadTodos({ project_id: projectId });
    },
    [loadTodos],
  );

  const loadTodosByLabel = useCallback(async () =>
    // label: string
    {
      // TODO: Label filtering would need to be implemented in the API
      // For now, we'll load all todos and filter client-side
      await loadTodos();
    }, [loadTodos]);

  return {
    // Filtered data
    todos,

    // Raw data from context
    allTodos,
    projects,
    labels,
    counts,

    // State
    loading,
    error,

    // Actions
    loadTodos,
    createTodo,
    updateTodo,
    deleteTodo,
    loadProjects,
    loadLabels,
    loadCounts,
    refreshAll,
    refresh,

    // Convenience methods
    loadTodayTodos,
    loadUpcomingTodos,
    loadCompletedTodos,
    loadTodosByPriority,
    loadTodosByProject,
    loadTodosByLabel,
  };
}
