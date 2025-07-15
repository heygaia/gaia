// Base message types to eliminate redundancy across chat bubble and conversation types

import React, { Dispatch } from "react";

import { SystemPurpose } from "@/features/chat/api/chatApi";
import { FileData } from "@/types/shared/fileTypes";

import {
    CalendarDeleteOptions,
    CalendarEditOptions,
    CalendarOptions,
} from "./calendarTypes";
import { EmailComposeData, EmailFetchData } from "./mailTypes";
import {
    DeepResearchResults,
    SearchResults,
} from "./searchTypes";
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

// Base interface containing all common fields shared across message types
export interface BaseMessageData {
    message_id: string;
    date?: string;
    pinned?: boolean;

    // Web search related fields
    searchWeb?: boolean;
    deepSearchWeb?: boolean;
    pageFetchURLs?: string[];

    // File related fields
    fileIds?: string[];
    fileData?: FileData[];

    // Tool related fields
    selectedTool?: string | null;
    toolCategory?: string | null;

    // All tool data fields - centralized in one place
    calendar_options?: CalendarOptions[] | null;
    calendar_delete_options?: CalendarDeleteOptions[] | null;
    calendar_edit_options?: CalendarEditOptions[] | null;
    email_compose_data?: EmailComposeData | null;
    email_fetch_data?: EmailFetchData | null
    weather_data?: WeatherData | null;
    search_results?: SearchResults | null;
    deep_research_results?: DeepResearchResults | null;
    image_data?: ImageData | null;
    todo_data?: TodoToolData | null;
    document_data?: DocumentData | null;
    code_data?: CodeData | null;
    memory_data?: MemoryData | null;
    goal_data?: GoalDataMessageType | null;
    google_docs_data?: GoogleDocsData | null;

    // System flag
    isConvoSystemGenerated?: boolean;
}

// Type for image data used in UI callbacks
export interface SetImageDataType {
    src: string; // corresponds to url in ImageData
    prompt: string;
    improvedPrompt: string; // corresponds to improved_prompt in ImageData
}

// User-specific message data
export interface UserMessageData extends BaseMessageData {
    text?: string;
    file?: File | null | string;
    filename?: string;
}

// Bot-specific message data with UI callbacks
export interface BotMessageData extends BaseMessageData {
    text: string;
    loading?: boolean;
    disclaimer?: string;
    filename?: string;
    systemPurpose?: SystemPurpose;

    // UI callback functions
    setOpenImage: React.Dispatch<React.SetStateAction<boolean>>;
    setImageData: Dispatch<React.SetStateAction<SetImageDataType>>;
    onOpenMemoryModal?: () => void;
}

// Message type for conversations (combines user and bot data)
export interface ConversationMessage extends BaseMessageData {
    type: "user" | "bot";
    response: string; // The main content field for conversations
    loading?: boolean;
    disclaimer?: string;
}

// Re-export all tool data types for convenience
export type {
    CalendarDeleteOptions,
    CalendarEditOptions,
    CalendarOptions,
    CodeData,
    DeepResearchResults,
    DocumentData,
    EmailComposeData,
    GoalDataMessageType,
    GoogleDocsData,
    ImageData,
    MemoryData,
    SearchResults,
    TodoToolData,
    WeatherData,
};
