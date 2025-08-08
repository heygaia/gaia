"use client";

import Spinner from "@/components/ui/shadcn/spinner";
import TodoDetailSheet from "@/features/todo/components/TodoDetailSheet";
import TodoHeader from "@/features/todo/components/TodoHeader";
import TodoList from "@/features/todo/components/TodoList";
import { useTodosPage } from "@/features/todo/hooks/useTodosPage";
import { Todo, TodoFilters } from "@/types/features/todoTypes";

interface TodosPageLayoutProps {
  title: string;
  filters: TodoFilters;
  showCompleted?: boolean;
  customLoader?: () => Promise<Todo[]>;
}

export default function TodosPageLayout({ 
  title, 
  filters, 
  showCompleted = false,
  customLoader
}: TodosPageLayoutProps) {
  const {
    loading,
    selectedTodo,
    projects,
    incompleteTodos,
    completedTodos,
    handleTodoUpdate,
    handleTodoDelete,
    handleTodoEdit,
    handleTodoClick,
    handleCloseDetail,
    refresh,
  } = useTodosPage({ filters, customLoader });

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const displayTodos = showCompleted ? completedTodos : incompleteTodos;

  return (
    <div className="flex h-full w-full flex-col">
      <div className="w-full px-4">
        <TodoHeader title={title} todoCount={displayTodos.length} />
      </div>

      <div className="w-full flex-1 overflow-y-auto px-4">
        <TodoList
          todos={displayTodos}
          onTodoUpdate={handleTodoUpdate}
          onTodoDelete={handleTodoDelete}
          onTodoEdit={handleTodoEdit}
          onTodoClick={handleTodoClick}
          onRefresh={refresh}
        />
      </div>

      <TodoDetailSheet
        todo={selectedTodo}
        isOpen={!!selectedTodo}
        onClose={handleCloseDetail}
        onUpdate={handleTodoUpdate}
        onDelete={handleTodoDelete}
        projects={projects}
      />
    </div>
  );
}
