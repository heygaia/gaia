/**
 * Tool Registry - Tools Message Data Schema
 *
 * This registry provides the schema for all tool-specific message data.
 * It defines the TOOLS_MESSAGE_SCHEMA that is used by the base message registry
 * to create the complete message data structure.
 */



export interface ToolDataEntry {
  tool_name: string;
  tool_category: string;
  data: unknown;
  timestamp: string | null;
}

// Define all possible tool names for the renderers
export type ToolName =
  | "search_results"
  | "deep_research_results"
  | "weather_data"
  | "email_thread_data"
  | "email_fetch_data"
  | "email_compose_data"
  | "calendar_options"
  | "calendar_delete_options"
  | "calendar_edit_options"
  | "calendar_fetch_data"
  | "calendar_list_fetch_data"
  | "support_ticket_data"
  | "document_data"
  | "google_docs_data"
  | "code_data"
  | "todo_data"
  | "goal_data"
  | "notification_data";


export const TOOLS_MESSAGE_SCHEMA = {
  tool_data: undefined as ToolDataEntry[] | null | undefined,
};

export type ToolsMessageData = typeof TOOLS_MESSAGE_SCHEMA;
export type ToolsMessageKey = keyof typeof TOOLS_MESSAGE_SCHEMA;
export const TOOLS_MESSAGE_KEYS = Object.keys(
  TOOLS_MESSAGE_SCHEMA,
) as ToolsMessageKey[];
