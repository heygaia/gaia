// TextBubble.tsx
import { Chip } from "@heroui/chip";
import { AlertTriangleIcon, ArrowUpRight } from "lucide-react";

import { InternetIcon } from "@/components/shared/icons";
import DeepResearchResultsTabs from "@/features/chat/components/bubbles/bot/DeepResearchResultsTabs";
import SearchResultsTabs from "@/features/chat/components/bubbles/bot/SearchResultsTabs";
import CustomAnchor from "@/features/chat/components/code-block/CustomAnchor";
import { shouldShowTextBubble } from "@/features/chat/utils/messageContentUtils";
import { WeatherCard } from "@/features/weather/components/WeatherCard";
import { ChatBubbleBotProps } from "@/types/features/chatBubbleTypes";

import MarkdownRenderer from "../../interface/MarkdownRenderer";
import { CalendarDeleteSection } from "./CalendarDeleteSection";
import { CalendarEditSection } from "./CalendarEditSection";
import CalendarEventSection from "./CalendarEventSection";
import CodeExecutionSection from "./CodeExecutionSection";
import DocumentSection from "./DocumentSection";
import EmailComposeSection from "./EmailComposeSection";
import GoalSection, { type GoalAction } from "./GoalSection";
import GoogleDocsSection from "./GoogleDocsSection";
import TodoSection from "./TodoSection";

export default function TextBubble({
  text,
  searchWeb,
  deepSearchWeb,
  pageFetchURLs,
  disclaimer,
  calendar_options,
  calendar_delete_options,
  calendar_edit_options,
  email_compose_data,
  email_fetch_data,
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

      {shouldShowTextBubble(
        text,
        searchWeb,
        deepSearchWeb,
        pageFetchURLs,
        isConvoSystemGenerated,
        systemPurpose,
      ) && (
        <div className="chat_bubble bg-zinc-800">
          <div className="flex flex-col gap-3">
            {!!(searchWeb || search_results) && (
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

            {!!(deepSearchWeb || deep_research_results) && (
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

            {!!(pageFetchURLs && pageFetchURLs.length > 0) &&
              pageFetchURLs!.map((pageFetchURL, index) => (
                <Chip
                  key={index}
                  color="primary"
                  startContent={<ArrowUpRight color="#00bbff" height={20} />}
                  variant="flat"
                >
                  <div className="flex items-center gap-1 font-medium text-primary">
                    Fetched{" "}
                    <CustomAnchor href={pageFetchURL}>
                      {pageFetchURL.replace(/^https?:\/\//, "")}
                    </CustomAnchor>
                  </div>
                </Chip>
              ))}

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
    </>
  );
}
