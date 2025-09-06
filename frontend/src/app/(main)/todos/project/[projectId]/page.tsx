"use client";

import { useParams } from "next/navigation";
import { useMemo } from "react";

import TodoListPage from "@/features/todo/components/TodoListPage";
import { useTodoData } from "@/features/todo/hooks/useTodoData";

export default function ProjectTodosPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  // Get projects to find the project name
  const { projects } = useTodoData({ autoLoad: false });

  const project = useMemo(() => {
    return projects.find((p) => p.id === projectId);
  }, [projects, projectId]);

  const projectName = project?.name || "Project";

  return (
    <TodoListPage
      title={projectName}
      filters={{ project_id: projectId }}
      showCompleted={false}
    />
  );
}
