"use client";

import TodosPageLayout from "@/features/todo/components/TodosPageLayout";

export default function TodosPage() {
  return (
    <TodosPageLayout 
      title="Inbox" 
      filters={{}} // Empty filters = inbox (backend default)
    />
  );
}
