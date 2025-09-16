/**
 * Base Message Registry - Core Message Data Schema
 *
 * This registry defines the core message data schema that is shared across all message types.
 * It imports and extends the tools message schema to provide a complete message data structure.
 */

import { IntegrationConnectionData } from "@/types/features/integrationTypes";
import { WorkflowData } from "@/types/features/workflowTypes";
import { FileData } from "@/types/shared/fileTypes";

import { TOOLS_MESSAGE_SCHEMA } from "./toolRegistry";

/**
 * BASE_MESSAGE_SCHEMA defines all the fields for message data.
 * Each value is set as `undefined as type` (or similar) to:
 *   1. Allow TypeScript to infer the correct type for BaseMessageData.
 *   2. Represent optional/nullable fields for runtime and type generation.
 *   3. Enable DRY code for both runtime key extraction and type safety.
 */
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
