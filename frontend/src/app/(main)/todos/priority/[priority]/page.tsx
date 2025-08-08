"use client";

import { useParams } from "next/navigation";

import TodosPageLayout from "@/features/todo/components/TodosPageLayout";
import { Priority } from "@/types/features/todoTypes";

export default function PriorityTodosPage() {
  const params = useParams();
  const priority = params.priority as Priority;
  
  const priorityLabels = {
    [Priority.HIGH]: "High Priority",
    [Priority.MEDIUM]: "Medium Priority", 
    [Priority.LOW]: "Low Priority",
    [Priority.NONE]: "No Priority",
  };

  return (
    <TodosPageLayout 
      title={priorityLabels[priority] || "Priority"} 
      filters={{ priority }}
    />
  );
}