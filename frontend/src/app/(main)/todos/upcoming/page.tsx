"use client";

import { useEffect, useState } from "react";

import Spinner from "@/components/ui/shadcn/spinner";
import { todoApi } from "@/features/todo/api/todoApi";
import TodoDetailSheet from "@/features/todo/components/TodoDetailSheet";
import TodoHeader from "@/features/todo/components/TodoHeader";
import TodoList from "@/features/todo/components/TodoList";
import { useUrlTodoSelection } from "@/features/todo/hooks/useUrlTodoSelection";
import { Project, Todo, TodoUpdate } from "@/types/features/todoTypes";

export default function UpcomingTodosPage() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const { selectedTodoId, selectTodo, clearSelection } = useUrlTodoSelection();

  useEffect(() => {
    loadUpcomingTodos();
    loadProjects();
  }, []);

  const loadUpcomingTodos = async () => {
    setLoading(true);
    try {
      // Use the unified todos endpoint with upcoming filter
      const todoList = await todoApi.getAllTodos({ due_this_week: true });
      setTodos(todoList);
    } catch (error) {
      console.error("Failed to load upcoming todos:", error);
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
      setTodos((prev) =>
        prev.map((todo) => (todo.id === todoId ? updatedTodo : todo)),
      );
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

  const handleTodoEdit = (todo: Todo) => {
    selectTodo(todo.id);
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  // Only show todos that are due in the future and not completed
  const upcomingTodos = todos.filter(
    (t) => t.due_date && new Date(t.due_date) >= new Date() && !t.completed,
  );

  return (
    <div className="flex h-full w-full flex-col">
      <div className="w-full px-4">
        <TodoHeader title="Upcoming" todoCount={upcomingTodos.length} />
      </div>

      <div className="w-full flex-1 overflow-y-auto px-4">
        <TodoList
          todos={upcomingTodos}
          onTodoUpdate={handleTodoUpdate}
          onTodoDelete={handleTodoDelete}
          onTodoEdit={handleTodoEdit}
          onTodoClick={(todo) => selectTodo(todo.id)}
          onRefresh={loadUpcomingTodos}
        />
      </div>

      {/* Todo Detail Sheet */}
      <TodoDetailSheet
        todo={
          selectedTodoId
            ? todos.find((t) => t.id === selectedTodoId) || null
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
}
