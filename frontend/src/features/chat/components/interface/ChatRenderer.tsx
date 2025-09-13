import { Spinner } from "@heroui/spinner";
import { useParams, useSearchParams } from "next/navigation";
import React, { useEffect, useMemo, useRef, useState } from "react";

import CreatedByGAIABanner from "@/features/chat/components/banners/CreatedByGAIABanner";
import ChatBubbleBot from "@/features/chat/components/bubbles/bot/ChatBubbleBot";
import SearchedImageDialog from "@/features/chat/components/bubbles/bot/SearchedImageDialog";
import ChatBubbleUser from "@/features/chat/components/bubbles/user/ChatBubbleUser";
import GeneratedImageSheet from "@/features/chat/components/image/GeneratedImageSheet";
import MemoryModal from "@/features/chat/components/memory/MemoryModal";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useConversationList } from "@/features/chat/hooks/useConversationList";
import { useLoading } from "@/features/chat/hooks/useLoading";
import { useLoadingText } from "@/features/chat/hooks/useLoadingText";
import {
  filterEmptyMessagePairs,
  isBotMessageEmpty,
} from "@/features/chat/utils/messageContentUtils";
import { getMessageProps } from "@/features/chat/utils/messagePropsUtils";
import { getToolCategoryIcon } from "@/features/chat/utils/toolIcons";
import {
  ChatBubbleBotProps,
  SetImageDataType,
} from "@/types/features/chatBubbleTypes";
import { MessageType } from "@/types/features/convoTypes";
import { getRandomThinkingMessage } from "@/utils/playfulThinking";

import { DateSeparator } from "./DateSeparator";
import { formatMessageDate, isDifferentDay } from "../../utils/dateUtils";

export default function ChatRenderer() {
  const { convoMessages } = useConversation();
  const { conversations } = useConversationList();
  const [openGeneratedImage, setOpenGeneratedImage] = useState<boolean>(false);
  const [openMemoryModal, setOpenMemoryModal] = useState<boolean>(false);
  const searchParams = useSearchParams();
  const messageId = searchParams.get("messageId");
  const { isLoading } = useLoading();
  const { loadingText, toolInfo } = useLoadingText();
  const { id: convoIdParam } = useParams<{ id: string }>();
  const scrolledToMessageRef = useRef<string | null>(null);
  const [imageData, setImageData] = useState<SetImageDataType>({
    src: "",
    prompt: "",
    improvedPrompt: "",
  });

  const conversation = useMemo(() => {
    return conversations.find(
      (convo) => convo.conversation_id === convoIdParam,
    );
  }, [conversations, convoIdParam]);

  // Create options object for getMessageProps
  const messagePropsOptions = {
    conversation,
    setImageData,
    setOpenGeneratedImage,
    setOpenMemoryModal,
  };

  // Filter out empty message pairs
  const filteredMessages = useMemo(() => {
    if (!convoMessages) return [];

    return filterEmptyMessagePairs(
      convoMessages,
      conversation?.is_system_generated || false,
      conversation?.system_purpose,
    );
  }, [
    convoMessages,
    conversation?.is_system_generated,
    conversation?.system_purpose,
  ]);

  useEffect(() => {
    if (
      messageId &&
      filteredMessages.length > 0 &&
      scrolledToMessageRef.current !== messageId
    ) {
      scrollToMessage(messageId);
      scrolledToMessageRef.current = messageId;
    }
  }, [messageId, filteredMessages]);

  const scrollToMessage = (messageId: string) => {
    if (!messageId) return;

    const messageElement = document.getElementById(messageId);

    if (!messageElement) return;

    messageElement.scrollIntoView({ behavior: "smooth", block: "start" });
    messageElement.style.transition = "all 0.3s ease";

    setTimeout(() => {
      messageElement.style.scale = "1.07";

      setTimeout(() => {
        messageElement.style.scale = "1";
      }, 300);
    }, 700);
  };

  return (
    <>
      <title id="chat_title">
        {`${
          conversations.find((convo) => convo.conversation_id === convoIdParam)
            ?.description || "New chat"
        } | GAIA`}
      </title>

      <GeneratedImageSheet
        imageData={imageData}
        openImage={openGeneratedImage}
        setOpenImage={setOpenGeneratedImage}
      />

      <MemoryModal
        isOpen={openMemoryModal}
        onClose={() => setOpenMemoryModal(false)}
      />

      <SearchedImageDialog />

      <CreatedByGAIABanner show={conversation?.is_system_generated === true} />

      {filteredMessages?.map((message: MessageType, index: number) => {
        let messageProps = null;

        if (message.type === "bot")
          messageProps = getMessageProps(message, "bot", messagePropsOptions);
        else if (message.type === "user")
          messageProps = getMessageProps(message, "user", messagePropsOptions);

        if (!messageProps) return null; // Skip rendering if messageProps is null

        // Check if we need to show a date separator
        const showDateSeparator =
          index === 0 ||
          (message.date &&
            filteredMessages[index - 1]?.date &&
            isDifferentDay(message.date, filteredMessages[index - 1].date!));

        const messageElement =
          message.type === "bot" &&
          !isBotMessageEmpty(messageProps as ChatBubbleBotProps) ? (
            <ChatBubbleBot
              key={message.message_id || index}
              {...getMessageProps(message, "bot", messagePropsOptions)}
            />
          ) : (
            <ChatBubbleUser
              key={message.message_id || index}
              {...messageProps}
            />
          );

        return (
          <React.Fragment key={`message-group-${message.message_id || index}`}>
            {showDateSeparator && message.date && (
              <DateSeparator date={formatMessageDate(message.date)} />
            )}
            {messageElement}
          </React.Fragment>
        );
      })}
      {isLoading && (
        <div className="flex items-center gap-4 pt-3 pl-[44px] text-sm font-medium">
          {toolInfo?.toolCategory && (
            <>
              {getToolCategoryIcon(toolInfo.toolCategory, {
                size: 18,
                width: 18,
                height: 18,
              })}
            </>
          )}
          <span>{loadingText || getRandomThinkingMessage()}</span>
          <Spinner variant="dots" color="primary" />
        </div>
      )}
    </>
  );
}
