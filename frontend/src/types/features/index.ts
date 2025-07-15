// Central export file for all feature types

// Base message types - the core types that eliminate redundancy
export type {
    BaseMessageData,
    BotMessageData,
    ConversationMessage,
    SetImageDataType,
    UserMessageData,
} from "./baseMessageTypes";

// Legacy types that now extend base types (for backwards compatibility)
export type {
    ChatBubbleBotProps,
    ChatBubbleUserProps,
} from "./chatBubbleTypes";
export type {
    ConversationType,
} from "./convoTypes";

// All tool-specific types
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
} from "./baseMessageTypes";

// Other feature types
export type * from "./goalTypes";
export type * from "./noteTypes";
export type * from "./notificationTypes";
export type * from "./pinTypes";
export type * from "./todoTypes";
