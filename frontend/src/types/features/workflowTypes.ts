// Workflow-related types for message data

export interface WorkflowStepData {
  id: string;
  title: string;
  description: string;
  tool_name: string;
  tool_category: string;
}

export interface WorkflowData {
  id: string;
  title: string;
  description: string;
  steps: WorkflowStepData[];
}
