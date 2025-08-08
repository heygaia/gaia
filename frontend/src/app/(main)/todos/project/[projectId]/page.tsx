"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { todoApi } from "@/features/todo/api/todoApi";
import TodosPageLayout from "@/features/todo/components/TodosPageLayout";
import { Project } from "@/types/features/todoTypes";

export default function ProjectTodosPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  
  const [projectName, setProjectName] = useState<string>("Project");

  useEffect(() => {
    // Load project name for title
    const loadProjectName = async () => {
      try {
        const projects = await todoApi.getAllProjects();
        const project = projects.find(p => p.id === projectId);
        setProjectName(project?.name || "Project");
      } catch (error) {
        console.error("Failed to load project name:", error);
      }
    };
    
    if (projectId) {
      loadProjectName();
    }
  }, [projectId]);

  return (
    <TodosPageLayout 
      title={projectName} 
      filters={{ project_id: projectId }}
    />
  );
}