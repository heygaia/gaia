// Tool data types for various AI-powered features

// Define image data structure for image generation
export type ImageData = {
  url: string;
  prompt?: string;
  improved_prompt?: string | null;
};

// Define document data structure for document processing
export type DocumentData = {
  filename: string;
  url: string;
  is_plain_text: boolean;
  title: string;
  metadata: Record<string, unknown>;
};

// Define memory data structure for memory operations
export type MemoryData = {
  operation?: string;
  status?: string;
  results?: Array<{
    id: string;
    content: string;
    relevance_score?: number;
    metadata?: Record<string, unknown>;
  }>;
  memories?: Array<{
    id: string;
    content: string;
    metadata?: Record<string, unknown>;
    created_at?: string;
  }>;
  count?: number;
  content?: string;
  memory_id?: string;
  error?: string;
};

// Define goal data structure for goal operations
export type GoalDataMessageType = {
  goals?: Array<{
    id: string;
    title: string;
    description?: string;
    progress?: number;
    roadmap?: {
      nodes: Array<{
        id: string;
        data: {
          title?: string;
          label?: string;
          isComplete?: boolean;
          type?: string;
          subtask_id?: string;
        };
      }>;
      edges: Array<{
        id: string;
        source: string;
        target: string;
      }>;
    };
    created_at?: string;
    todo_project_id?: string;
    todo_id?: string;
  }>;
  action?: string;
  message?: string;
  goal_id?: string;
  deleted_goal_id?: string;
  stats?: {
    total_goals: number;
    goals_with_roadmaps: number;
    total_tasks: number;
    completed_tasks: number;
    overall_completion_rate: number;
    active_goals: Array<{
      id: string;
      title: string;
      progress: number;
    }>;
    active_goals_count: number;
  };
  error?: string;
};

// Define code execution data structure
export type CodeData = {
  language: string;
  code: string;
  output?: {
    stdout: string;
    stderr: string;
    results: string[];
    error: string | null;
  } | null;
  charts?: Array<{
    id: string;
    url: string;
    text: string;
    type?: string;
    title?: string;
    description?: string;
    chart_data?: {
      type: string;
      title: string;
      x_label: string;
      y_label: string;
      x_unit?: string | null;
      y_unit?: string | null;
      elements: Array<{
        label: string;
        value: number;
        group: string;
      }>;
    };
  }> | null;
  status?: "executing" | "completed" | "error";
};

// Define Google Docs data structure for Google Docs operations
export type GoogleDocsData = {
  document: {
    id: string;
    title: string;
    url: string;
    created_time: string;
    modified_time: string;
    type: string;
  };
  query?: string | null;
  action: string;
  message: string;
  type: string;
};

// Unified tool data entry structure (matches backend TypedDict)
export interface ToolDataEntry {
  tool_name: string;
  tool_category: string;
  data: unknown;
  timestamp: string | null;
}
