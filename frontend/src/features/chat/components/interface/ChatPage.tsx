"use client";

import {
  useParams,
  usePathname,
  useRouter,
  useSearchParams,
} from "next/navigation";
import React, { useEffect } from "react";

import { FileDropModal } from "@/features/chat/components/files/FileDropModal";
import { ComposerProvider } from "@/features/chat/contexts/ComposerContext";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { fetchMessages } from "@/features/chat/utils/chatUtils";
import { useDragAndDrop } from "@/hooks/ui/useDragAndDrop";

import { useScrollBehavior, useChatLayout } from "./hooks";
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
    conversation,
    hasMessages,
    chatRef,
    cardStackSectionRef,
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
    if (convoIdParam) {
      fetchMessages(convoIdParam, updateConvoMessages, router).then(() => {
        setTimeout(scrollToBottom, 500);
      });
    } else {
      clearMessages();
      if (pathname !== "/c") router.push("/c");
    }

    if (inputRef?.current) inputRef.current.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [convoIdParam]);

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
              cardStackSectionRef={cardStackSectionRef}
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
            />
          </>
        )}
      </div>
    </ComposerProvider>
  );
});

export default ChatPage;
