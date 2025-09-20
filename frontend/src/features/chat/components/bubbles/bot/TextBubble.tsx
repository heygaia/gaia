// TextBubble.tsx
import { Chip } from "@heroui/chip";
import { AlertTriangleIcon } from "lucide-react";

import { InternetIcon } from "@/components/shared/icons";
import CalendarListCard from "@/features/calendar/components/CalendarListCard";
import CalendarListFetchCard from "@/features/calendar/components/CalendarListFetchCard";
import DeepResearchResultsTabs from "@/features/chat/components/bubbles/bot/DeepResearchResultsTabs";
import EmailThreadCard from "@/features/chat/components/bubbles/bot/EmailThreadCard";
import SearchResultsTabs from "@/features/chat/components/bubbles/bot/SearchResultsTabs";
import { shouldShowTextBubble } from "@/features/chat/utils/messageContentUtils";
import EmailListCard from "@/features/mail/components/EmailListCard";
import { WeatherCard } from "@/features/weather/components/WeatherCard";
import { ChatBubbleBotProps } from "@/types/features/chatBubbleTypes";
import MarkdownRenderer from "../../interface/MarkdownRenderer";
import { CalendarDeleteSection } from "./CalendarDeleteSection";
import { CalendarEditSection } from "./CalendarEditSection";
import CalendarEventSection from "./CalendarEventSection";
import CodeExecutionSection from "./CodeExecutionSection";
import DocumentSection from "./DocumentSection";
import EmailComposeSection from "./EmailComposeSection";
import FollowUpActions from "./FollowUpActions";
import GoalSection from "./goals/GoalSection";
import { GoalAction } from "./goals/types";
import GoogleDocsSection from "./GoogleDocsSection";
import SupportTicketSection from "./SupportTicketSection";
import TodoSection from "./TodoSection";
import {
  SearchResults,
  DeepResearchResults,
  WeatherData,
  EmailThreadData,
  DocumentData,
  GoogleDocsData,
  CodeData,
  TodoToolData,
  GoalDataMessageType,
  EmailComposeData,
  CalendarOptions,
  CalendarDeleteOptions,
  CalendarEditOptions,
} from "@/types";
import {
  CalendarFetchData,
  CalendarListFetchData,
} from "@/types/features/calendarTypes";
import { EmailFetchData } from "@/types/features/mailTypes";
import { SupportTicketData } from "@/types/features/supportTypes";

// Map of tool_name -> renderer function
// This avoids scattering switch/case or if/else across the component
const TOOL_RENDERERS: Record<
  string,
  (data: unknown, index: number) => React.ReactNode
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
  weather: (data, index) => (
    <WeatherCard
      key={`tool-weather-${index}`}
      weatherData={data as WeatherData}
    />
  ),

  // Email
  email_thread: (data, index) => (
    <EmailThreadCard
      key={`tool-email-thread-${index}`}
      emailThreadData={data as EmailThreadData}
    />
  ),
  email_fetch: (data, index) => (
    <EmailListCard
      key={`tool-email-fetch-${index}`}
      emails={(Array.isArray(data) ? data : [data]) as EmailFetchData[]}
    />
  ),
  email_compose: (data, index) => (
    <EmailComposeSection
      key={`tool-email-compose-${index}`}
      email_compose_data={
        (Array.isArray(data) ? data : [data]) as EmailComposeData[]
      }
    />
  ),

  // Calendar
  calendar: (data, index) => {
    return (
      <CalendarEventSection
        key={`tool-cal-options-${index}`}
        calendar_options={data as CalendarOptions[]}
      />
    );
  },
  calendar_delete: (data, index) => {
    return (
      <CalendarDeleteSection
        key={`tool-cal-del-${index}`}
        calendar_delete_options={data as CalendarDeleteOptions[]}
      />
    );
  },
  calendar_edit: (data, index) => {
    return (
      <CalendarEditSection
        key={`tool-cal-edit-${index}`}
        calendar_edit_options={data as CalendarEditOptions[]}
      />
    );
  },
  calendar_fetch: (data, index) => (
    <CalendarListCard
      key={`tool-cal-fetch-${index}`}
      events={(Array.isArray(data) ? data : [data]) as CalendarFetchData[]}
    />
  ),
  calendar_list_fetch: (data, index) => (
    <CalendarListFetchCard
      key={`tool-cal-list-${index}`}
      calendars={
        (Array.isArray(data) ? data : [data]) as CalendarListFetchData[]
      }
    />
  ),

  // Support ticket
  support_ticket: (data, index) => (
    <SupportTicketSection
      key={`tool-support-${index}`}
      support_ticket_data={data as SupportTicketData[]}
    />
  ),

  // Documents & Code
  document: (data, index) => (
    <DocumentSection
      key={`tool-doc-${index}`}
      document_data={data as DocumentData}
    />
  ),
  google_docs: (data, index) => (
    <GoogleDocsSection
      key={`tool-gdocs-${index}`}
      google_docs_data={data as GoogleDocsData}
    />
  ),
  code: (data, index) => (
    <CodeExecutionSection
      key={`tool-code-${index}`}
      code_data={data as CodeData}
    />
  ),

  todo: (data, index) => {
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
  goal: (data, index) => {
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
};

export default function TextBubble({
  text,
  disclaimer,
  calendar_options,
  calendar_delete_options,
  calendar_edit_options,
  email_compose_data,
  email_fetch_data,
  email_thread_data,
  support_ticket_data,
  calendar_fetch_data,
  calendar_list_fetch_data,
  weather_data,
  todo_data,
  goal_data,
  code_data,
  search_results,
  deep_research_results,
  document_data,
  google_docs_data,
  tool_data,
  isConvoSystemGenerated,
  systemPurpose,
  follow_up_actions,
  loading,
}: ChatBubbleBotProps) {
  return (
    <>
      {!!search_results && (
        <SearchResultsTabs search_results={search_results!} />
      )}

      {!!deep_research_results && (
        <DeepResearchResultsTabs
          deep_research_results={deep_research_results!}
        />
      )}

      {!!weather_data && <WeatherCard weatherData={weather_data!} />}

      {!!email_thread_data && (
        <EmailThreadCard emailThreadData={email_thread_data} />
      )}

      {/* Unified tool_data rendering via registry */}
      {tool_data &&
        tool_data.map((entry, index) => {
          const render = TOOL_RENDERERS[entry.tool_name];
          if (!render) return null;
          return <>{render(entry.data, index)}</>;
        })}

      {shouldShowTextBubble(text, isConvoSystemGenerated, systemPurpose) && (
        <div className="chat_bubble bg-zinc-800">
          <div className="flex flex-col gap-3">
            {!!search_results && (
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

            {!!deep_research_results && (
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
                  <AlertTriangleIcon className="text-warning-500" height={17} />
                }
                variant="flat"
              >
                {disclaimer!}
              </Chip>
            )}
          </div>
        </div>
      )}

      {!!calendar_options && (
        <CalendarEventSection calendar_options={calendar_options!} />
      )}

      {!!calendar_delete_options && (
        <CalendarDeleteSection
          calendar_delete_options={calendar_delete_options!}
        />
      )}

      {!!calendar_edit_options && (
        <CalendarEditSection calendar_edit_options={calendar_edit_options!} />
      )}

      {!!email_compose_data && (
        <EmailComposeSection email_compose_data={email_compose_data!} />
      )}

      {!!support_ticket_data && (
        <SupportTicketSection support_ticket_data={support_ticket_data!} />
      )}

      {!!email_fetch_data && <EmailListCard emails={email_fetch_data} />}

      {!!calendar_fetch_data && (
        <CalendarListCard events={calendar_fetch_data!} />
      )}

      {!!calendar_list_fetch_data && (
        <CalendarListFetchCard calendars={calendar_list_fetch_data} />
      )}

      {!!todo_data && (
        <TodoSection
          todos={todo_data!.todos}
          projects={todo_data!.projects}
          stats={todo_data!.stats}
          action={todo_data!.action}
          message={todo_data!.message}
        />
      )}

      {/* Document Data - render all instances */}
      {!!document_data && <DocumentSection document_data={document_data!} />}

      {/* Google Docs Data - render all instances */}
      {!!google_docs_data && (
        <GoogleDocsSection google_docs_data={google_docs_data!} />
      )}

      {/* Goal Data - render all instances */}
      {!!goal_data && (
        <GoalSection
          goals={goal_data!.goals}
          stats={goal_data!.stats}
          action={goal_data!.action as GoalAction}
          message={goal_data!.message}
          goal_id={goal_data!.goal_id}
          deleted_goal_id={goal_data!.deleted_goal_id}
          error={goal_data!.error}
        />
      )}

      {/* Code Data - render all instances */}
      {!!code_data && <CodeExecutionSection code_data={code_data!} />}

      {!!follow_up_actions && follow_up_actions?.length > 0 && (
        <FollowUpActions actions={follow_up_actions} loading={!!loading} />
      )}
    </>
  );
}
