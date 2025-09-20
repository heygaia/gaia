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
import { ChatBubbleBotProps } from "@/types/features/chatBubbleTypes";

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

export default function TextBubble({
  text,
  disclaimer,
  calendar_options,
  calendar_delete_options,
  calendar_edit_options,
  email_compose_data,
  email_fetch_data,
  email_thread_data,
  email_sent_data,
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
  notification_data,
  isConvoSystemGenerated,
  systemPurpose,
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

      {!!email_sent_data && <EmailSentCard emailSentData={email_sent_data} />}

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
                        {!!search_results && index === 0 && (
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

                        {!!deep_research_results && index === 0 && (
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

      {!!document_data && <DocumentSection document_data={document_data!} />}

      {!!google_docs_data && (
        <GoogleDocsSection google_docs_data={google_docs_data!} />
      )}

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

      {!!code_data && <CodeExecutionSection code_data={code_data!} />}

      {!!notification_data && (
        <NotificationListSection
          notifications={notification_data.notifications}
          title="Your Notifications"
        />
      )}
    </>
  );
}
