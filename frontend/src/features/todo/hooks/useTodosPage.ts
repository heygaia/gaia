"use client";

import { useEffect, useState } from "react";

import { todoApi } from "@/features/todo/api/todoApi";
import {
  Project,
  Todo,
  TodoFilters,
  TodoUpdate,
} from "@/types/features/todoTypes";

interface UseTodosPageOptions {
  filters: TodoFilters;
  autoLoad?: boolean;
  customLoader?: () => Promise<Todo[]>; // For special cases like label loading
}

// Helper function to check if a todo should be removed from current view after update
function checkShouldRemoveFromView(
  updatedTodo: Todo, 
  filters: TodoFilters, 
  updates: TodoUpdate
): boolean {
  // If priority filter is set and priority changed
  if (filters.priority && updates.priority && updates.priority !== filters.priority) {
    return true;
  }
  
  // If project filter is set and project changed
  if (filters.project_id && updates.project_id && updates.project_id !== filters.project_id) {
    return true;
  }
  
  // If completed filter is set and completion status changed
  if (filters.completed !== undefined && updates.completed !== undefined && updates.completed !== filters.completed) {
    return true;
  }
  
  // If labels filter is set and labels changed
  if (filters.labels && updates.labels) {
    const hasRequiredLabel = updates.labels.some(label => filters.labels?.includes(label));
    if (!hasRequiredLabel) {
      return true;
    }
  }
  
  return false;
}

export function useTodosPage({ filters, autoLoad = true, customLoader }: UseTodosPageOptions) {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTodoId, setSelectedTodoId] = useState<string | null>(null);

  const loadTodos = async () => {
    setLoading(true);
    try {
      const todoList = customLoader 
        ? await customLoader()
        : await todoApi.getAllTodos(filters);
      setTodos(todoList);
    } catch (error) {
      console.error("Failed to load todos:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const projectList = await todoApi.getAllProjects();
      setProjects(projectList);
    } catch (error) {
      console.error("Failed to load projects:", error);
    }
  };

  const handleTodoUpdate = async (todoId: string, updates: TodoUpdate) => {
    try {
      const updatedTodo = await todoApi.updateTodo(todoId, updates);
      
      // Check if the updated todo still matches our filters
      const shouldRemoveFromView = checkShouldRemoveFromView(updatedTodo, filters, updates);
      
      if (shouldRemoveFromView) {
        setTodos(prev => prev.filter(todo => todo.id !== todoId));
        // Close detail sheet if this todo was selected
        if (selectedTodoId === todoId) {
          setSelectedTodoId(null);
        }
      } else {
        setTodos(prev =>
          prev.map(todo => (todo.id === todoId ? updatedTodo : todo))
        );
      }
    } catch (error) {
      console.error("Failed to update todo:", error);
    }
  };

  const handleTodoDelete = async (todoId: string) => {
    try {
      await todoApi.deleteTodo(todoId);
      setTodos(prev => prev.filter(todo => todo.id !== todoId));
      if (selectedTodoId === todoId) {
        setSelectedTodoId(null);
      }
    } catch (error) {
      console.error("Failed to delete todo:", error);
    }
  };

  const handleTodoEdit = (todo: Todo) => {
    setSelectedTodoId(todo.id);
  };

  const handleTodoClick = (todo: Todo) => {
    setSelectedTodoId(todo.id);
  };

  const handleCloseDetail = () => {
    setSelectedTodoId(null);
  };

  const refresh = () => {
    loadTodos();
  };

  // Auto-load on mount and when filters change
  useEffect(() => {
    if (autoLoad) {
      loadTodos();
      loadProjects();
    }
  }, [JSON.stringify(filters)]);

  return {
    // State
    todos,
    projects,
    loading,
    selectedTodoId,
    selectedTodo: selectedTodoId 
      ? todos.find(t => t.id === selectedTodoId) || null 
      : null,
    
    // Actions
    loadTodos,
    handleTodoUpdate,
    handleTodoDelete,
    handleTodoEdit,
    handleTodoClick,
    handleCloseDetail,
    refresh,
    
    // Computed
    incompleteTodos: todos.filter(t => !t.completed),
    completedTodos: todos.filter(t => t.completed),
  };
}
