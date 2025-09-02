/**
 * Workflow API service for unified workflow management.
 * Provides functions to interact with the workflow backend API.
 */

import { apiService } from "@/lib/api";

export interface WorkflowStepType {
  id: string;
  title: string;
  tool_name: string;
  tool_category: string;
  description: string;
  tool_inputs: Record<string, unknown>;
  order: number;
  executed_at?: string;
  result?: Record<string, unknown>;
}

export interface TriggerConfig {
  type: "manual" | "schedule" | "email" | "calendar" | "webhook";
  cron_expression?: string;
  timezone?: string;
  next_run?: string;
  email_patterns?: string[];
  email_labels?: string[];
  calendar_patterns?: string[];
  webhook_url?: string;
  webhook_secret?: string;
  enabled: boolean;
}

export interface ExecutionConfig {
  method: "chat" | "background" | "hybrid";
  timeout_seconds: number;
  max_retries: number;
  retry_delay_seconds: number;
  notify_on_completion: boolean;
  notify_on_failure: boolean;
}

export interface WorkflowMetadata {
  created_from: "chat" | "modal" | "todo" | "template" | "api";
  template_id?: string;
  related_todo_id?: string;
  related_conversation_id?: string;
  tags: string[];
  category?: string;
  total_executions: number;
  successful_executions: number;
  last_execution_at?: string;
  average_execution_time?: number;
}

export interface CommunityWorkflowStep {
  title: string;
  tool_name: string;
  tool_category: string;
  description: string;
}

export interface CommunityWorkflow {
  id: string;
  title: string;
  description: string;
  steps: CommunityWorkflowStep[];
  upvotes: number;
  is_upvoted: boolean;
  created_at: string;
  creator: {
    id: string;
    name: string;
    avatar?: string;
  };
}

export interface CommunityWorkflowsResponse {
  workflows: CommunityWorkflow[];
  total: number;
}

export interface Workflow {
  id: string;
  title: string;
  description: string;
  steps: WorkflowStepType[];
  trigger_config: TriggerConfig;
  execution_config: ExecutionConfig;
  metadata: WorkflowMetadata;
  activated: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  last_executed_at?: string;
  current_step_index: number;
  execution_logs: string[];
  error_message?: string;

  // Community features
  is_public?: boolean;
  created_by?: string;
  upvotes?: number;
  upvoted_by?: string[];
}

export interface CreateWorkflowRequest {
  title: string;
  description: string;
  trigger_config: TriggerConfig;
  execution_config?: ExecutionConfig;
  metadata?: Partial<WorkflowMetadata>;
  generate_immediately?: boolean;
}

export interface WorkflowExecutionRequest {
  execution_method?: "chat" | "background" | "hybrid";
  context?: Record<string, unknown>;
}

export interface WorkflowStatusResponse {
  workflow_id: string;
  activated: boolean;
  current_step_index: number;
  total_steps: number;
  progress_percentage: number;
  last_updated: string;
  error_message?: string;
  logs: string[];
}

export const workflowApi = {
  // Create a new workflow
  createWorkflow: async (
    request: CreateWorkflowRequest,
  ): Promise<{ workflow: Workflow; message: string }> => {
    return apiService.post<{ workflow: Workflow; message: string }>(
      "/workflows",
      request,
      {
        errorMessage: "Failed to create workflow",
      },
    );
  },

  // List workflows with filtering
  listWorkflows: async (params?: {
    activated?: boolean;
    source?: string;
    limit?: number;
    skip?: number;
  }): Promise<{
    workflows: Workflow[];
    total_count: number;
    page: number;
    page_size: number;
  }> => {
    const searchParams = new URLSearchParams();
    if (params?.activated !== undefined)
      searchParams.append("activated", params.activated.toString());
    if (params?.source) searchParams.append("source", params.source);
    if (params?.limit) searchParams.append("limit", params.limit.toString());
    if (params?.skip) searchParams.append("skip", params.skip.toString());

    const queryString = searchParams.toString();
    const url = queryString ? `/workflows?${queryString}` : "/workflows";

    return apiService.get<{
      workflows: Workflow[];
      total_count: number;
      page: number;
      page_size: number;
    }>(url);
  },

  // Get a specific workflow
  getWorkflow: async (
    workflowId: string,
    options?: { silent?: boolean },
  ): Promise<{ workflow: Workflow; message: string }> => {
    return apiService.get<{ workflow: Workflow; message: string }>(
      `/workflows/${workflowId}`,
      {
        silent: options?.silent,
      },
    );
  },

  // Update a workflow
  updateWorkflow: async (
    workflowId: string,
    updates: Partial<CreateWorkflowRequest>,
  ): Promise<{ workflow: Workflow; message: string }> => {
    return apiService.put<{ workflow: Workflow; message: string }>(
      `/workflows/${workflowId}`,
      updates,
      {
        successMessage: "Workflow updated successfully",
        errorMessage: "Failed to update workflow",
      },
    );
  },

  // Delete a workflow
  deleteWorkflow: async (workflowId: string): Promise<{ message: string }> => {
    return apiService.delete<{ message: string }>(`/workflows/${workflowId}`, {
      successMessage: "Workflow deleted successfully",
      errorMessage: "Failed to delete workflow",
    });
  },

  // Activate a workflow
  activateWorkflow: async (
    workflowId: string,
  ): Promise<{ workflow: Workflow; message: string }> => {
    return apiService.post<{ workflow: Workflow; message: string }>(
      `/workflows/${workflowId}/activate`,
      {},
      {
        successMessage: "Workflow activated successfully",
        errorMessage: "Failed to activate workflow",
      },
    );
  },

  // Deactivate a workflow
  deactivateWorkflow: async (
    workflowId: string,
  ): Promise<{ workflow: Workflow; message: string }> => {
    return apiService.post<{ workflow: Workflow; message: string }>(
      `/workflows/${workflowId}/deactivate`,
      {},
      {
        successMessage: "Workflow deactivated successfully",
        errorMessage: "Failed to deactivate workflow",
      },
    );
  },

  // Regenerate workflow steps
  regenerateWorkflowSteps: async (
    workflowId: string,
    options?: {
      reason?: string;
      force_different_tools?: boolean;
    },
  ): Promise<{ workflow: Workflow; message: string }> => {
    return apiService.post<{ workflow: Workflow; message: string }>(
      `/workflows/${workflowId}/regenerate-steps`,
      {
        reason: options?.reason,
        force_different_tools: options?.force_different_tools ?? true,
      },
      {
        errorMessage: "Failed to regenerate workflow steps",
      },
    );
  },

  // Execute a workflow
  executeWorkflow: async (
    workflowId: string,
    request?: WorkflowExecutionRequest,
  ): Promise<{
    execution_id: string;
    message: string;
    estimated_completion_time?: string;
  }> => {
    return apiService.post<{
      execution_id: string;
      message: string;
      estimated_completion_time?: string;
    }>(`/workflows/${workflowId}/execute`, request || {}, {
      successMessage: "Workflow execution started",
      errorMessage: "Failed to execute workflow",
    });
  },

  // Get workflow status
  getWorkflowStatus: async (
    workflowId: string,
  ): Promise<WorkflowStatusResponse> => {
    return apiService.get<WorkflowStatusResponse>(
      `/workflows/${workflowId}/status`,
      {
        silent: true, // Don't show success/error toasts for polling
      },
    );
  },

  // Create workflow from todo (migration helper)
  createWorkflowFromTodo: async (
    todoId: string,
    todoTitle: string,
    todoDescription?: string,
  ): Promise<{ workflow: Workflow; message: string }> => {
    return apiService.post<{ workflow: Workflow; message: string }>(
      "/workflows/from-todo",
      {
        todo_id: todoId,
        todo_title: todoTitle,
        todo_description: todoDescription,
      },
      {
        successMessage: "Workflow created from todo successfully",
        errorMessage: "Failed to create workflow from todo",
      },
    );
  },

  // Publish workflow to community
  publishWorkflow: async (
    workflowId: string,
  ): Promise<{ message: string; workflow_id: string }> => {
    return apiService.post<{ message: string; workflow_id: string }>(
      `/workflows/${workflowId}/publish`,
      {},
      {
        successMessage: "Workflow published to community",
        errorMessage: "Failed to publish workflow",
      },
    );
  },

  // Unpublish workflow from community
  unpublishWorkflow: async (
    workflowId: string,
  ): Promise<{ message: string }> => {
    return apiService.post<{ message: string }>(
      `/workflows/${workflowId}/unpublish`,
      {},
      {
        successMessage: "Workflow unpublished from community",
        errorMessage: "Failed to unpublish workflow",
      },
    );
  },

  // Get public workflows from community
  getCommunityWorkflows: async (
    limit: number = 20,
    offset: number = 0,
  ): Promise<CommunityWorkflowsResponse> => {
    return apiService.get<CommunityWorkflowsResponse>(
      `/workflows/community?limit=${limit}&offset=${offset}`,
      {
        errorMessage: "Failed to fetch community workflows",
      },
    );
  },

  // Upvote/downvote a community workflow
  upvoteWorkflow: async (
    workflowId: string,
  ): Promise<{ message: string; action: string }> => {
    return apiService.post<{ message: string; action: string }>(
      `/workflows/${workflowId}/upvote`,
      {},
      {
        silent: true, // Disable generic toast - component will handle success messages
        errorMessage: "Failed to update vote",
      },
    );
  },
};
