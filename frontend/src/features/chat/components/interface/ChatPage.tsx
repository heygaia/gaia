"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import React, { useEffect } from "react";

import { FileDropModal } from "@/features/chat/components/files/FileDropModal";
import { ComposerProvider } from "@/features/chat/contexts/ComposerContext";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { chatApi } from "@/features/chat/api/chatApi";
import { fetchMessages } from "@/features/chat/utils/chatUtils";
import { useDragAndDrop } from "@/hooks/ui/useDragAndDrop";

import { useChatLayout, useScrollBehavior } from "./hooks";
import { ChatWithMessages, NewChatLayout } from "./layouts";
import { ScrollButtons } from "./scroll";

const ChatPage = React.memo(function MainChat() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const messageId = searchParams.get("messageId");

  const { updateConvoMessages, clearMessages } = useConversation();

  // Use our custom hooks
  const {
    conversation: _conversation,
    hasMessages,
    chatRef,
    cardStackSectionRef: _cardStackSectionRef,
    dummySectionRef,
    inputRef,
    droppedFiles,
    setDroppedFiles,
    fileUploadRef,
    appendToInputRef,
    convoIdParam,
  } = useChatLayout();

  const {
    scrollContainerRef,
    scrollToBottom,
    handleScroll,
    handleNewChatScroll,
  } = useScrollBehavior(hasMessages, messageId);

  // Drag and drop functionality
  const { isDragging, dragHandlers } = useDragAndDrop({
    onDrop: (files: File[]) => {
      setDroppedFiles(files);
      if (fileUploadRef.current) {
        fileUploadRef.current.handleDroppedFiles(files);
        fileUploadRef.current.openFileUploadModal();
      }
    },
    multiple: true,
  });

  // Message fetching effect
  useEffect(() => {
    const loadMessages = async () => {
      if (convoIdParam) {
        try {
          const messages = await chatApi.fetchMessages(convoIdParam);
          updateConvoMessages(messages);
        } catch (error) {
          console.error("Failed to fetch messages:", error);
        }
      } else {
        clearMessages();
      }
    };

    loadMessages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [convoIdParam]);

  // Handle pending prompt from global composer
  useEffect(() => {
    const pendingPrompt = localStorage.getItem("pendingPrompt");
    if (pendingPrompt && appendToInputRef.current) {
      appendToInputRef.current(pendingPrompt);
      localStorage.removeItem("pendingPrompt");
    }
  }, []);

  // Common composer props
  const composerProps = {
    inputRef,
    scrollToBottom,
    fileUploadRef,
    appendToInputRef,
    droppedFiles,
    onDroppedFilesProcessed: () => setDroppedFiles([]),
    hasMessages,
  };

  // Function to append text to input
  const appendToInput = (text: string) => {
    if (appendToInputRef.current) {
      appendToInputRef.current(text);
    }
  };

  return (
    <ComposerProvider value={{ appendToInput }}>
      <div className="flex h-full flex-col">
        <FileDropModal isDragging={isDragging} />

        {hasMessages ? (
          <>
            <ChatWithMessages
              scrollContainerRef={scrollContainerRef}
              chatRef={chatRef}
              handleScroll={handleScroll}
              dragHandlers={dragHandlers}
              composerProps={composerProps}
            />
            <ScrollButtons
              containerRef={scrollContainerRef}
              onScrollToBottom={scrollToBottom}
              hasMessages={hasMessages}
            />
          </>
        ) : (
          <>
            <NewChatLayout
              scrollContainerRef={scrollContainerRef}
              dummySectionRef={dummySectionRef}
              handleNewChatScroll={handleNewChatScroll}
              dragHandlers={dragHandlers}
              composerProps={composerProps}
            />
            <ScrollButtons
              containerRef={scrollContainerRef}
              onScrollToBottom={scrollToBottom}
              hasMessages={hasMessages}
              gridSectionRef={dummySectionRef}
            />
          </>
        )}
      </div>
    </ComposerProvider>
  );
});

export default ChatPage;
