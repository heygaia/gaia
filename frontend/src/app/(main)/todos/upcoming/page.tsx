"use client";

import TodosPageLayout from "@/features/todo/components/TodosPageLayout";

export default function UpcomingTodosPage() {
  return (
    <TodosPageLayout 
      title="Upcoming" 
      filters={{ due_this_week: true }}
    />
  );
}
