"use client";

import { useMemo } from "react";

import Spinner from "@/components/ui/shadcn/spinner";
import TodoDetailSheet from "@/features/todo/components/TodoDetailSheet";
import TodoHeader from "@/features/todo/components/TodoHeader";
import TodoList from "@/features/todo/components/TodoList";
import { useTodoData } from "@/features/todo/hooks/useTodoData";
import { useUrlTodoSelection } from "@/features/todo/hooks/useUrlTodoSelection";
import { Todo, TodoFilters, TodoUpdate } from "@/types/features/todoTypes";

interface TodoListPageProps {
  title: string;
  filters?: TodoFilters;
  filterTodos?: (todos: Todo[]) => Todo[];
  showCompleted?: boolean;
}

export default function TodoListPage({
  title,
  filters,
  filterTodos,
  showCompleted = false,
}: TodoListPageProps) {
  const { selectedTodoId, selectTodo, clearSelection } = useUrlTodoSelection();

  const {
    todos: allTodos,
    projects,
    loading,
    updateTodo,
    deleteTodo,
    refresh,
  } = useTodoData({ filters, autoLoad: true });

  // Apply additional client-side filtering if provided
  const todos = useMemo(() => {
    let filteredTodos = allTodos;

    // Apply custom filter function if provided
    if (filterTodos) {
      filteredTodos = filterTodos(filteredTodos);
    }

    // Filter by completion status unless showCompleted is true
    if (!showCompleted) {
      filteredTodos = filteredTodos.filter((todo) => !todo.completed);
    }

    return filteredTodos;
  }, [allTodos, filterTodos, showCompleted]);

  const handleTodoUpdate = async (todoId: string, updates: TodoUpdate) => {
    try {
      await updateTodo(todoId, updates);
    } catch (error) {
      console.error("Failed to update todo:", error);
    }
  };

  const handleTodoDelete = async (todoId: string) => {
    try {
      await deleteTodo(todoId);
      // If the deleted todo was selected, close the detail sheet
      if (selectedTodoId === todoId) {
        clearSelection();
      }
    } catch (error) {
      console.error("Failed to delete todo:", error);
    }
  };

  const handleTodoEdit = (todo: Todo) => {
    selectTodo(todo.id);
  };

  const handleTodoClick = (todo: Todo) => {
    selectTodo(todo.id);
  };

  if (loading && todos.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col">
      <div className="w-full px-4">
        <TodoHeader title={title} todoCount={todos.length} />
      </div>

      <div className="w-full flex-1 overflow-y-auto px-4">
        <TodoList
          todos={todos}
          onTodoUpdate={handleTodoUpdate}
          onTodoDelete={handleTodoDelete}
          onTodoEdit={handleTodoEdit}
          onTodoClick={handleTodoClick}
          onRefresh={refresh}
        />
      </div>

      {/* Todo Detail Sheet */}
      <TodoDetailSheet
        todo={
          selectedTodoId
            ? allTodos.find((t) => t.id === selectedTodoId) || null
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
