import { Chip } from "@heroui/chip";
import Link from "next/link";
import React from "react";

import {
  BubbleChatIcon,
  BubbleConversationChatIcon,
  StickyNote01Icon,
} from "@/components/shared/icons";
import { parseDate2 } from "@/utils/date/dateUtils";

import { CommandItem } from "../../../components/ui/shadcn/command";

interface SearchMessageResult {
  conversation_id: string;
  message: {
    message_id: string;
    type: "bot" | "user";
    date: string;
  };
  snippet: string;
}

interface SearchConversationResult {
  conversation_id: string;
  description: string;
}

interface SearchNoteResult {
  id: string;
  snippet: string;
}

type SearchResultType =
  | SearchMessageResult
  | SearchConversationResult
  | SearchNoteResult;

interface SearchCardConfig<T extends SearchResultType> {
  icon: React.ReactNode;
  linkTo: (result: T) => string;
  bodyContent: (result: T) => React.ReactNode;
  footerContent?: (result: T) => React.ReactNode;
}

interface SearchCardProps {
  result: SearchResultType;
  type: "message" | "conversation" | "note";
  config?: SearchCardConfig<SearchResultType>;
  className?: string;
}

const messageConfig: SearchCardConfig<SearchMessageResult> = {
  icon: (
    <BubbleChatIcon className="min-h-[22px] min-w-[22px]" color="#9b9b9b" />
  ),
  linkTo: (result) => `/c/${result.conversation_id}`,
  bodyContent: (result) => (
    <>
      <div className="flex items-center gap-2">
        <Chip
          color={result.message.type === "bot" ? "primary" : "default"}
          size="sm"
        >
          {result.message.type === "bot" ? "From GAIA" : "From You"}
        </Chip>
      </div>
      <CommandItem className="w-full cursor-pointer truncate px-0! py-1! data-[selected='true']:bg-transparent!">
        {result.snippet}
      </CommandItem>
    </>
  ),
  footerContent: (result) => parseDate2(result.message.date),
};

const conversationConfig: SearchCardConfig<SearchConversationResult> = {
  icon: (
    <BubbleConversationChatIcon
      className="min-h-[22px] min-w-[22px]"
      color="#9b9b9b"
    />
  ),
  linkTo: (result) => `/c/${result.conversation_id}`,
  bodyContent: (result) => (
    <CommandItem className="w-full cursor-pointer truncate px-0! py-1! data-[selected='true']:bg-transparent!">
      {result.description}
    </CommandItem>
  ),
};

const noteConfig: SearchCardConfig<SearchNoteResult> = {
  icon: (
    <StickyNote01Icon className="min-h-[22px] min-w-[22px]" color="#9b9b9b" />
  ),
  linkTo: (result) => `/notes/${result.id}`,
  bodyContent: (result) => (
    <CommandItem className="w-full cursor-pointer truncate px-0! py-1! data-[selected='true']:bg-transparent!">
      {result.snippet}
    </CommandItem>
  ),
};

const defaultConfigs: Record<string, SearchCardConfig<SearchResultType>> = {
  message: messageConfig as SearchCardConfig<SearchResultType>,
  conversation: conversationConfig as SearchCardConfig<SearchResultType>,
  note: noteConfig as SearchCardConfig<SearchResultType>,
};

export function SearchCard({
  result,
  type,
  config,
  className,
}: SearchCardProps) {
  const { icon, linkTo, bodyContent, footerContent } =
    config || defaultConfigs[type];

  const hasContent =
    (result as SearchNoteResult).snippet ||
    (result as SearchConversationResult).description;

  if (!hasContent) return null;

  const key =
    "message" in result && result.message?.message_id
      ? result.message.message_id
      : "conversation_id" in result
        ? result.conversation_id
        : (result as SearchNoteResult).id;

  return (
    <Link
      key={key}
      className={`my-2 flex h-full flex-row items-center gap-2 overflow-hidden rounded-xl bg-zinc-800 p-2 px-3 transition-colors hover:bg-zinc-700 ${className}`}
      href={linkTo(result)}
    >
      <div className="min-h-[22px] min-w-[22px]">{icon}</div>
      <div className="flex-1">{bodyContent(result)}</div>
      {footerContent && (
        <div className="ml-auto text-sm text-foreground-500">
          {footerContent(result)}
        </div>
      )}
    </Link>
  );
}
