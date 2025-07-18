"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import Spinner from "@/components/ui/shadcn/spinner";
import { todoApi } from "@/features/todo/api/todoApi";
import TodoHeader from "@/features/todo/components/TodoHeader";
import TodoList from "@/features/todo/components/TodoList";
import {
  Priority,
  Todo,
  TodoFilters,
  TodoUpdate,
} from "@/types/features/todoTypes";

export default function PriorityTodosPage() {
  const params = useParams();
  const priority = params.priority as Priority;

  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPriorityTodos = useCallback(async () => {
    setLoading(true);
    try {
      const filters: TodoFilters = {
        priority: priority,
      };
      const todoList = await todoApi.getAllTodos(filters);
      setTodos(todoList);
    } catch (error) {
      console.error("Failed to load priority todos:", error);
    } finally {
      setLoading(false);
    }
  }, [priority]);

  useEffect(() => {
    if (priority) {
      loadPriorityTodos();
    }
  }, [priority, loadPriorityTodos]);

  const handleTodoUpdate = async (todoId: string, updates: TodoUpdate) => {
    try {
      const updatedTodo = await todoApi.updateTodo(todoId, updates);

      // If the todo's priority changed, remove it from this view
      if (updates.priority && updates.priority !== priority) {
        setTodos((prev) => prev.filter((todo) => todo.id !== todoId));
      } else {
        setTodos((prev) =>
          prev.map((todo) => (todo.id === todoId ? updatedTodo : todo)),
        );
      }
    } catch (error) {
      console.error("Failed to update todo:", error);
    }
  };

  const handleTodoDelete = async (todoId: string) => {
    try {
      await todoApi.deleteTodo(todoId);
      setTodos((prev) => prev.filter((todo) => todo.id !== todoId));
    } catch (error) {
      console.error("Failed to delete todo:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const priorityLabels = {
    [Priority.HIGH]: "High Priority",
    [Priority.MEDIUM]: "Medium Priority",
    [Priority.LOW]: "Low Priority",
    [Priority.NONE]: "No Priority",
  };

  return (
    <div className="flex h-full w-full flex-col">
      <div className="w-full" style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <TodoHeader
          title={priorityLabels[priority] || "Priority"}
          todoCount={todos.length}
        />
      </div>

      <div
        className="flex-1 overflow-y-auto px-4"
        style={{ maxWidth: "1200px", margin: "0 auto", width: "100%" }}
      >
        <TodoList
          todos={todos}
          onTodoUpdate={handleTodoUpdate}
          onTodoDelete={handleTodoDelete}
          onRefresh={loadPriorityTodos}
        />
      </div>
    </div>
  );
}
