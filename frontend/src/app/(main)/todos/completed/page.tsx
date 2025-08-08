"use client";

import TodosPageLayout from "@/features/todo/components/TodosPageLayout";

export default function CompletedTodosPage() {
  return (
    <TodosPageLayout 
      title="Completed" 
      filters={{ completed: true }}
      showCompleted={true}
    />
  );
}
