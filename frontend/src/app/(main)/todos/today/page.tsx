"use client";

import TodosPageLayout from "@/features/todo/components/TodosPageLayout";

export default function TodayTodosPage() {
  return (
    <TodosPageLayout 
      title="Today" 
      filters={{ due_today: true }}
    />
  );
}
