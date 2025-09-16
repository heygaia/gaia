/**
 * Tool Registry - Tools Message Data Schema
 *
 * This registry provides the schema for all tool-specific message data.
 * It defines the TOOLS_MESSAGE_SCHEMA that is used by the base message registry
 * to create the complete message data structure.
 */

import {
  CalendarDeleteOptions,
  CalendarEditOptions,
  CalendarFetchData,
  CalendarListFetchData,
  CalendarOptions,
} from "@/types/features/calendarTypes";
import {
  EmailComposeData,
  EmailFetchData,
  EmailSentData,
  EmailThreadData,
} from "@/types/features/mailTypes";
import {
  DeepResearchResults,
  SearchResults,
} from "@/types/features/searchTypes";
import { SupportTicketData } from "@/types/features/supportTypes";
import { TodoToolData } from "@/types/features/todoToolTypes";
import {
  CodeData,
  DocumentData,
  GoalDataMessageType,
  GoogleDocsData,
  ImageData,
  MemoryData,
} from "@/types/features/toolDataTypes";
import { WeatherData } from "@/types/features/weatherTypes";

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
  email_sent_data: undefined as EmailSentData | null | undefined,
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

export type ToolsMessageData = typeof TOOLS_MESSAGE_SCHEMA;
export type ToolsMessageKey = keyof typeof TOOLS_MESSAGE_SCHEMA;
export const TOOLS_MESSAGE_KEYS = Object.keys(
  TOOLS_MESSAGE_SCHEMA,
) as ToolsMessageKey[];
