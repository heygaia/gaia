"use client";

import TodoListPage from "@/features/todo/components/TodoListPage";

export default function CompletedTodosPage() {
  return (
    <TodoListPage
      title="Completed"
      filters={{ completed: true }}
      showCompleted={true}
    />
  );
}
