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
import {
  renderArrayToolData,
  renderToolData,
} from "@/utils/toolDataNormalizer";

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
  isConvoSystemGenerated,
  systemPurpose,
  follow_up_actions,
  loading,
}: ChatBubbleBotProps) {
  return (
    <>
      {/* Search Results - render all instances */}
      {renderToolData(search_results, (result, index) => (
        <SearchResultsTabs key={index} search_results={result} />
      ))}

      {/* Deep Research Results - render all instances */}
      {renderToolData(deep_research_results, (result, index) => (
        <DeepResearchResultsTabs key={index} deep_research_results={result} />
      ))}

      {/* Weather Data - render all instances */}
      {renderToolData(weather_data, (data, index) => (
        <WeatherCard key={index} weatherData={data} />
      ))}

      {/* Email Thread Data - render all instances */}
      {renderToolData(email_thread_data, (thread, index) => (
        <EmailThreadCard key={index} emailThreadData={thread} />
      ))}

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

      {/* Calendar Options - handle array tool data */}
      {renderArrayToolData(calendar_options, (options, index) => (
        <CalendarEventSection key={index} calendar_options={options} />
      ))}

      {/* Calendar Delete Options - handle array tool data */}
      {renderArrayToolData(calendar_delete_options, (options, index) => (
        <CalendarDeleteSection key={index} calendar_delete_options={options} />
      ))}

      {/* Calendar Edit Options - handle array tool data */}
      {renderArrayToolData(calendar_edit_options, (options, index) => (
        <CalendarEditSection key={index} calendar_edit_options={options} />
      ))}

      {/* Email Compose Data - handle array tool data */}
      {renderArrayToolData(email_compose_data, (data, index) => (
        <EmailComposeSection key={index} email_compose_data={data} />
      ))}

      {/* Support Ticket Data - handle array tool data */}
      {renderArrayToolData(support_ticket_data, (data, index) => (
        <SupportTicketSection key={index} support_ticket_data={data} />
      ))}

      {/* Email Fetch Data - handle array tool data */}
      {renderArrayToolData(email_fetch_data, (emails, index) => (
        <EmailListCard key={index} emails={emails} />
      ))}

      {/* Calendar Fetch Data - handle array tool data */}
      {renderArrayToolData(calendar_fetch_data, (events, index) => (
        <CalendarListCard key={index} events={events} />
      ))}

      {/* Calendar List Fetch Data - handle array tool data */}
      {renderArrayToolData(calendar_list_fetch_data, (calendars, index) => (
        <CalendarListFetchCard key={index} calendars={calendars} />
      ))}

      {/* Todo Data - render all instances */}
      {renderToolData(todo_data, (data, index) => (
        <TodoSection
          key={index}
          todos={data.todos}
          projects={data.projects}
          stats={data.stats}
          action={data.action}
          message={data.message}
        />
      ))}

      {/* Document Data - render all instances */}
      {renderToolData(document_data, (data, index) => (
        <DocumentSection key={index} document_data={data} />
      ))}

      {/* Google Docs Data - render all instances */}
      {renderToolData(google_docs_data, (data, index) => (
        <GoogleDocsSection key={index} google_docs_data={data} />
      ))}

      {/* Goal Data - render all instances */}
      {renderToolData(goal_data, (data, index) => (
        <GoalSection
          key={index}
          goals={data.goals}
          stats={data.stats}
          action={data.action as GoalAction}
          message={data.message}
          goal_id={data.goal_id}
          deleted_goal_id={data.deleted_goal_id}
          error={data.error}
        />
      ))}

      {/* Code Data - render all instances */}
      {renderToolData(code_data, (data, index) => (
        <CodeExecutionSection key={index} code_data={data} />
      ))}

      {!!follow_up_actions && follow_up_actions?.length > 0 && (
        <FollowUpActions actions={follow_up_actions} loading={!!loading} />
      )}
    </>
  );
}
