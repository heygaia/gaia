// TextBubble.tsx
import { Chip } from "@heroui/chip";
import { AlertTriangleIcon } from "lucide-react";

import { InternetIcon } from "@/components/shared/icons";

import CalendarListCard from "@/features/calendar/components/CalendarListCard";
import CalendarListFetchCard from "@/features/calendar/components/CalendarListFetchCard";
import DeepResearchResultsTabs from "@/features/chat/components/bubbles/bot/DeepResearchResultsTabs";
import EmailThreadCard from "@/features/chat/components/bubbles/bot/EmailThreadCard";
import SearchResultsTabs from "@/features/chat/components/bubbles/bot/SearchResultsTabs";
import { splitMessageByBreaks } from "@/features/chat/utils/messageBreakUtils";
import { shouldShowTextBubble } from "@/features/chat/utils/messageContentUtils";
import EmailListCard from "@/features/mail/components/EmailListCard";
import EmailSentCard from "@/features/mail/components/EmailSentCard";
import { WeatherCard } from "@/features/weather/components/WeatherCard";
import {
  CalendarDeleteOptions,
  CalendarEditOptions,
  CalendarOptions,
  CodeData,
  DeepResearchResults,
  DocumentData,
  EmailComposeData,
  EmailThreadData,
  GoalDataMessageType,
  GoogleDocsData,
  SearchResults,
  TodoToolData,
  WeatherData,
} from "@/types";
import {
  CalendarFetchData,
  CalendarListFetchData,
} from "@/types/features/calendarTypes";
import { ChatBubbleBotProps } from "@/types/features/chatBubbleTypes";
import { EmailFetchData } from "@/types/features/mailTypes";
import { SupportTicketData } from "@/types/features/supportTypes";

import MarkdownRenderer from "../../interface/MarkdownRenderer";
import { CalendarDeleteSection } from "./CalendarDeleteSection";
import { CalendarEditSection } from "./CalendarEditSection";
import CalendarEventSection from "./CalendarEventSection";
import CodeExecutionSection from "./CodeExecutionSection";
import DocumentSection from "./DocumentSection";
import EmailComposeSection from "./EmailComposeSection";
import GoalSection from "./goals/GoalSection";
import { GoalAction } from "./goals/types";
import GoogleDocsSection from "./GoogleDocsSection";
import NotificationListSection from "./NotificationListSection";
import SupportTicketSection from "./SupportTicketSection";
import TodoSection from "./TodoSection";
import { ToolName } from "@/config/registries/toolRegistry";

// Map of tool_name -> renderer function for unified tool_data rendering
const TOOL_RENDERERS: Partial<
  Record<ToolName, (data: any, index: number) => React.ReactNode>
> = {
  // Search
  search_results: (data, index) => (
    <SearchResultsTabs
      key={`tool-search-${index}`}
      search_results={data as SearchResults}
    />
  ),
  deep_research_results: (data, index) => (
    <DeepResearchResultsTabs
      key={`tool-deep-search-${index}`}
      deep_research_results={data as DeepResearchResults}
    />
  ),

  // Weather
  weather_data: (data, index) => (
    <WeatherCard
      key={`tool-weather-${index}`}
      weatherData={data as WeatherData}
    />
  ),

  // Email
  email_thread_data: (data, index) => (
    <EmailThreadCard
      key={`tool-email-thread-${index}`}
      emailThreadData={data as EmailThreadData}
    />
  ),
  email_fetch_data: (data, index) => (
    <EmailListCard
      key={`tool-email-fetch-${index}`}
      emails={(Array.isArray(data) ? data : [data]) as EmailFetchData[]}
    />
  ),
  email_compose_data: (data, index) => (
    <EmailComposeSection
      key={`tool-email-compose-${index}`}
      email_compose_data={
        (Array.isArray(data) ? data : [data]) as EmailComposeData[]
      }
    />
  ),

  // Calendar
  calendar_options: (data, index) => {
    return (
      <CalendarEventSection
        key={`tool-cal-options-${index}`}
        calendar_options={data as CalendarOptions[]}
      />
    );
  },
  calendar_delete_options: (data, index) => {
    return (
      <CalendarDeleteSection
        key={`tool-cal-del-${index}`}
        calendar_delete_options={data as CalendarDeleteOptions[]}
      />
    );
  },
  calendar_edit_options: (data, index) => {
    return (
      <CalendarEditSection
        key={`tool-cal-edit-${index}`}
        calendar_edit_options={data as CalendarEditOptions[]}
      />
    );
  },
  calendar_fetch_data: (data, index) => (
    <CalendarListCard
      key={`tool-cal-fetch-${index}`}
      events={(Array.isArray(data) ? data : [data]) as CalendarFetchData[]}
    />
  ),
  calendar_list_fetch_data: (data, index) => (
    <CalendarListFetchCard
      key={`tool-cal-list-${index}`}
      calendars={
        (Array.isArray(data) ? data : [data]) as CalendarListFetchData[]
      }
    />
  ),

  // Support ticket
  support_ticket_data: (data, index) => (
    <SupportTicketSection
      key={`tool-support-${index}`}
      support_ticket_data={data as SupportTicketData[]}
    />
  ),

  // Documents & Code
  document_data: (data, index) => (
    <DocumentSection
      key={`tool-doc-${index}`}
      document_data={data as DocumentData}
    />
  ),
  google_docs_data: (data, index) => (
    <GoogleDocsSection
      key={`tool-gdocs-${index}`}
      google_docs_data={data as GoogleDocsData}
    />
  ),
  code_data: (data, index) => (
    <CodeExecutionSection
      key={`tool-code-${index}`}
      code_data={data as CodeData}
    />
  ),

  todo_data: (data, index) => {
    const t = data as TodoToolData;
    return (
      <TodoSection
        key={`tool-todo-${index}`}
        todos={t.todos}
        projects={t.projects}
        stats={t.stats}
        action={t.action}
        message={t.message}
      />
    );
  },
  goal_data: (data, index) => {
    const g = data as GoalDataMessageType;
    return (
      <GoalSection
        key={`tool-goal-${index}`}
        goals={g.goals}
        stats={g.stats}
        action={g.action as GoalAction}
        message={g.message}
        goal_id={g.goal_id}
        deleted_goal_id={g.deleted_goal_id}
        error={g.error}
      />
    );
  },
  notification_data: (data, index) => (
    <NotificationListSection
      key={`tool-notifications-${index}`}
      notifications={(data as { notifications: any[] }).notifications}
      title="Your Notifications"
    />
  ),
};

export default function TextBubble({
  text,
  disclaimer,
  tool_data,
  isConvoSystemGenerated,
  systemPurpose,
}: ChatBubbleBotProps) {
  // Check if we have search results from tool_data for chip display
  const hasSearchResults = tool_data?.some(
    (entry) => entry.tool_name === "search_results",
  );
  const hasDeepResearchResults = tool_data?.some(
    (entry) => entry.tool_name === "deep_research_results",
  );

  return (
    <>
      {/* Unified tool_data rendering via registry */}
      {tool_data &&
        tool_data.map((entry, index) => {
          const render = TOOL_RENDERERS[entry.tool_name as ToolName];
          if (!render) return null;
          return <>{render(entry.data, index)}</>;
        })}

      {shouldShowTextBubble(text, isConvoSystemGenerated, systemPurpose) &&
        (() => {
          // Split text content by NEW_MESSAGE_BREAK tokens
          const textParts = splitMessageByBreaks(text?.toString() || "");

          if (textParts.length > 1) {
            // Render multiple iMessage-style bubbles for split content
            return (
              <div className="flex flex-col">
                {textParts.map((part, index) => {
                  const isFirst = index === 0;
                  const isLast = index === textParts.length - 1;
                  // const isMiddle = !isFirst && !isLast;

                  // iMessage grouped styling classes
                  const groupedClasses = isFirst
                    ? "imessage-grouped-first mb-1.5"
                    : isLast
                      ? "imessage-grouped-last"
                      : "imessage-grouped-middle mb-1.5";

                  return (
                    <div
                      key={index}
                      className={`imessage-bubble imessage-from-them ${groupedClasses}`}
                    >
                      <div className="flex flex-col gap-3">
                        {hasSearchResults && index === 0 && (
                          <Chip
                            color="primary"
                            startContent={
                              <InternetIcon color="#00bbff" height={20} />
                            }
                            variant="flat"
                          >
                            <div className="flex items-center gap-1 font-medium text-primary">
                              Live Search Results from the Web
                            </div>
                          </Chip>
                        )}

                        {hasDeepResearchResults && index === 0 && (
                          <Chip
                            color="primary"
                            startContent={
                              <InternetIcon color="#00bbff" height={20} />
                            }
                            variant="flat"
                          >
                            <div className="flex items-center gap-1 font-medium text-primary">
                              Deep Search Results from the Web
                            </div>
                          </Chip>
                        )}

                        <MarkdownRenderer content={part} />

                        {!!disclaimer && index === textParts.length - 1 && (
                          <Chip
                            className="text-xs font-medium text-warning-500"
                            color="warning"
                            size="sm"
                            startContent={
                              <AlertTriangleIcon
                                className="text-warning-500"
                                height={17}
                              />
                            }
                            variant="flat"
                          >
                            {disclaimer!}
                          </Chip>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          }

          // Single iMessage bubble (normal behavior)
          return (
            <div className="imessage-bubble imessage-from-them">
              <div className="flex flex-col gap-3">
                {hasSearchResults && (
                  <Chip
                    color="primary"
                    startContent={<InternetIcon color="#00bbff" height={20} />}
                    variant="flat"
                  >
                    <div className="flex items-center gap-1 font-medium text-primary">
                      Live Search Results from the Web
                    </div>
                  </Chip>
                )}

                {hasDeepResearchResults && (
                  <Chip
                    color="primary"
                    startContent={<InternetIcon color="#00bbff" height={20} />}
                    variant="flat"
                  >
                    <div className="flex items-center gap-1 font-medium text-primary">
                      Deep Search Results from the Web
                    </div>
                  </Chip>
                )}

                {!!text && <MarkdownRenderer content={text.toString()} />}

                {!!disclaimer && (
                  <Chip
                    className="text-xs font-medium text-warning-500"
                    color="warning"
                    size="sm"
                    startContent={
                      <AlertTriangleIcon
                        className="text-warning-500"
                        height={17}
                      />
                    }
                    variant="flat"
                  >
                    {disclaimer!}
                  </Chip>
                )}
              </div>
            </div>
          );
        })()}
    </>
  );
}
