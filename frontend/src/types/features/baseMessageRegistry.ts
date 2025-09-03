// This registry provides a single source of truth for all message data keys and types.
// By defining BASE_MESSAGE_SCHEMA, we can generate both the runtime keys (BASE_MESSAGE_KEYS)
// and the TypeScript type (BaseMessageData) from one place, ensuring DRY and type-safe code.

import { FileData } from "@/types/shared/fileTypes";

import {
  CalendarDeleteOptions,
  CalendarEditOptions,
  CalendarFetchData,
  CalendarListFetchData,
  CalendarOptions,
} from "./calendarTypes";
import { IntegrationConnectionData } from "./integrationTypes";
import { EmailComposeData, EmailFetchData, EmailThreadData } from "./mailTypes";
import { DeepResearchResults, SearchResults } from "./searchTypes";
import { SupportTicketData } from "./supportTypes";
import { TodoToolData } from "./todoToolTypes";
import {
  CodeData,
  DocumentData,
  GoalDataMessageType,
  GoogleDocsData,
  ImageData,
  MemoryData,
} from "./toolDataTypes";
import { WeatherData } from "./weatherTypes";
import { WorkflowData } from "./workflowTypes";

export const TOOLS_MESSAGE_SCHEMA = {
  calendar_options: undefined as CalendarOptions[] | null | undefined,
  calendar_delete_options: undefined as
    | CalendarDeleteOptions[]
    | null
    | undefined,
  calendar_edit_options: undefined as CalendarEditOptions[] | null | undefined,
  email_compose_data: undefined as EmailComposeData[] | null | undefined,
  email_fetch_data: undefined as EmailFetchData[] | null | undefined,
  email_thread_data: undefined as EmailThreadData | null | undefined,
  support_ticket_data: undefined as SupportTicketData[] | null | undefined,
  weather_data: undefined as WeatherData | null | undefined,
  search_results: undefined as SearchResults | null | undefined,
  deep_research_results: undefined as DeepResearchResults | null | undefined,
  image_data: undefined as ImageData | null | undefined,
  todo_data: undefined as TodoToolData | null | undefined,
  document_data: undefined as DocumentData | null | undefined,
  code_data: undefined as CodeData | null | undefined,
  memory_data: undefined as MemoryData | null | undefined,
  goal_data: undefined as GoalDataMessageType | null | undefined,
  google_docs_data: undefined as GoogleDocsData | null | undefined,
  calendar_fetch_data: undefined as CalendarFetchData[] | null | undefined,
  calendar_list_fetch_data: undefined as
    | CalendarListFetchData[]
    | null
    | undefined,
};

// BASE_MESSAGE_SCHEMA defines all the fields for message data.
// Each value is set as `undefined as type` (or similar) to:
//   1. Allow TypeScript to infer the correct type for BaseMessageData.
//   2. Represent optional/nullable fields for runtime and type generation.
//   3. Enable DRY code for both runtime key extraction and type safety.
export const BASE_MESSAGE_SCHEMA = {
  message_id: "" as string, // required string field
  date: undefined as string | undefined,
  pinned: undefined as boolean | undefined,
  fileIds: undefined as string[] | undefined,
  fileData: undefined as FileData[] | undefined,
  selectedTool: undefined as string | null | undefined,
  toolCategory: undefined as string | null | undefined,
  selectedWorkflow: undefined as WorkflowData | null | undefined,
  isConvoSystemGenerated: undefined as boolean | undefined,
  follow_up_actions: undefined as string[] | undefined,
  integration_connection_required: undefined as
    | IntegrationConnectionData
    | null
    | undefined,
  ...TOOLS_MESSAGE_SCHEMA,
};

export type BaseMessageData = typeof BASE_MESSAGE_SCHEMA;
export type BaseMessageKey = keyof typeof BASE_MESSAGE_SCHEMA;
export const BASE_MESSAGE_KEYS = Object.keys(
  BASE_MESSAGE_SCHEMA,
) as BaseMessageKey[];

export type ToolsMessageData = typeof TOOLS_MESSAGE_SCHEMA;
export type ToolsMessageKey = keyof typeof TOOLS_MESSAGE_SCHEMA;
export const TOOLS_MESSAGE_KEYS = Object.keys(
  TOOLS_MESSAGE_SCHEMA,
) as ToolsMessageKey[];
