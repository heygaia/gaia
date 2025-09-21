"use client";

import { useSearchParams } from "next/navigation";
import React, { useEffect } from "react";

import { chatApi } from "@/features/chat/api/chatApi";
import { FileDropModal } from "@/features/chat/components/files/FileDropModal";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useDragAndDrop } from "@/hooks/ui/useDragAndDrop";
import {
  useComposerTextActions,
  usePendingPrompt,
} from "@/stores/composerStore";

import { useChatLayout, useScrollBehavior } from "./hooks";
import { ChatWithMessages, NewChatLayout } from "./layouts";
import { ScrollButtons } from "./scroll";

const ChatPage = React.memo(function MainChat() {
  const searchParams = useSearchParams();
  const messageId = searchParams.get("messageId");

  const { updateConvoMessages, clearMessages } = useConversation();
  const pendingPrompt = usePendingPrompt();
  const { clearPendingPrompt } = useComposerTextActions();

  // Use our custom hooks
  const {
    hasMessages,
    chatRef,
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
    if (pendingPrompt && appendToInputRef.current) {
      appendToInputRef.current(pendingPrompt);
      clearPendingPrompt();
    }
  }, [pendingPrompt, clearPendingPrompt, appendToInputRef]);

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

  return (
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
  );
});

export default ChatPage;
