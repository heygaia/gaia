"use client";

import { useParams } from "next/navigation";

import { todoApi } from "@/features/todo/api/todoApi";
import TodosPageLayout from "@/features/todo/components/TodosPageLayout";
import { useTodosPage } from "@/features/todo/hooks/useTodosPage";

export default function LabelTodosPage() {
  const params = useParams();
  const label = params.label as string;
  const decodedLabel = decodeURIComponent(label);

  // Use the hook but override the default behavior for labels since they use a different API
  const customLoader = async () => {
    return await todoApi.getTodosByLabel(decodedLabel);
  };

  return (
    <TodosPageLayout 
      title={`Label: ${decodedLabel}`} 
      filters={{ labels: [decodedLabel] }}
      customLoader={customLoader}
    />
  );
}