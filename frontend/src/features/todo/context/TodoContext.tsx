"use client";

import React, {
  createContext,
  useContext,
  useCallback,
  useState,
  ReactNode,
} from "react";

import { todoApi } from "@/features/todo/api/todoApi";
import {
  Todo,
  TodoCreate,
  TodoUpdate,
  TodoFilters,
  Project,
  Priority,
} from "@/types/features/todoTypes";

interface TodoCounts {
  inbox: number;
  today: number;
  upcoming: number;
  completed: number;
}

interface TodoContextState {
  // Data
  todos: Todo[];
  projects: Project[];
  labels: { name: string; count: number }[];
  counts: TodoCounts;

  // UI State
  loading: boolean;
  error: string | null;

  // Actions
  loadTodos: (filters?: TodoFilters) => Promise<void>;
  createTodo: (todoData: TodoCreate) => Promise<Todo>;
  updateTodo: (todoId: string, updates: TodoUpdate) => Promise<Todo>;
  deleteTodo: (todoId: string) => Promise<void>;
  loadProjects: () => Promise<void>;
  loadLabels: () => Promise<void>;
  loadCounts: () => Promise<void>;
  refreshAll: () => Promise<void>;
}

const TodoContext = createContext<TodoContextState | undefined>(undefined);

interface TodoProviderProps {
  children: ReactNode;
}

export function TodoProvider({ children }: TodoProviderProps) {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [labels, setLabels] = useState<{ name: string; count: number }[]>([]);
  const [counts, setCounts] = useState<TodoCounts>({
    inbox: 0,
    today: 0,
    upcoming: 0,
    completed: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTodos = useCallback(async (filters?: TodoFilters) => {
    setLoading(true);
    setError(null);
    try {
      const fetchedTodos = await todoApi.getAllTodos(filters);
      setTodos(fetchedTodos);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load todos");
      console.error("Failed to load todos:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createTodo = useCallback(
    async (todoData: TodoCreate): Promise<Todo> => {
      setError(null);
      try {
        const newTodo = await todoApi.createTodo(todoData);

        // Optimistically add to current list
        setTodos((prev) => [newTodo, ...prev]);

        // Refresh counts in background
        loadCounts().catch(console.error);

        return newTodo;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create todo");
        throw err;
      }
    },
    [],
  );

  const updateTodo = useCallback(
    async (todoId: string, updates: TodoUpdate): Promise<Todo> => {
      setError(null);

      // Store original for rollback
      const originalTodo = todos.find((t) => t.id === todoId);

      // Optimistic update
      setTodos((prev) =>
        prev.map((todo) =>
          todo.id === todoId ? { ...todo, ...updates } : todo,
        ),
      );

      try {
        const updatedTodo = await todoApi.updateTodo(todoId, updates);

        // Update with server response
        setTodos((prev) =>
          prev.map((todo) => (todo.id === todoId ? updatedTodo : todo)),
        );

        // Refresh counts if completion status changed
        if (
          updates.completed !== undefined &&
          originalTodo?.completed !== updates.completed
        ) {
          loadCounts().catch(console.error);
        }

        return updatedTodo;
      } catch (err) {
        // Rollback on error
        if (originalTodo) {
          setTodos((prev) =>
            prev.map((todo) => (todo.id === todoId ? originalTodo : todo)),
          );
        }
        setError(err instanceof Error ? err.message : "Failed to update todo");
        throw err;
      }
    },
    [todos],
  );

  const deleteTodo = useCallback(
    async (todoId: string): Promise<void> => {
      setError(null);

      // Store original for rollback
      const originalTodos = todos;

      // Optimistic delete
      setTodos((prev) => prev.filter((todo) => todo.id !== todoId));

      try {
        await todoApi.deleteTodo(todoId);

        // Refresh counts in background
        loadCounts().catch(console.error);
      } catch (err) {
        // Rollback on error
        setTodos(originalTodos);
        setError(err instanceof Error ? err.message : "Failed to delete todo");
        throw err;
      }
    },
    [todos],
  );

  const loadProjects = useCallback(async () => {
    setError(null);
    try {
      const fetchedProjects = await todoApi.getAllProjects();
      setProjects(fetchedProjects);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
      console.error("Failed to load projects:", err);
    }
  }, []);

  const loadLabels = useCallback(async () => {
    setError(null);
    try {
      const fetchedLabels = await todoApi.getAllLabels();
      setLabels(fetchedLabels);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load labels");
      console.error("Failed to load labels:", err);
    }
  }, []);

  const loadCounts = useCallback(async () => {
    setError(null);
    try {
      const fetchedCounts = await todoApi.getTodoCounts();
      setCounts(fetchedCounts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load counts");
      console.error("Failed to load counts:", err);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setError(null);
    try {
      await Promise.all([loadProjects(), loadLabels(), loadCounts()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh data");
      console.error("Failed to refresh all data:", err);
    }
  }, [loadProjects, loadLabels, loadCounts]);

  const value: TodoContextState = {
    // Data
    todos,
    projects,
    labels,
    counts,

    // UI State
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
  };

  return <TodoContext.Provider value={value}>{children}</TodoContext.Provider>;
}

export function useTodoContext(): TodoContextState {
  const context = useContext(TodoContext);
  if (context === undefined) {
    throw new Error("useTodoContext must be used within a TodoProvider");
  }
  return context;
}
