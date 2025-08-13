"use client";

import Image from "next/image";
import {
  useParams,
  usePathname,
  useRouter,
  useSearchParams,
} from "next/navigation";
import React, { useEffect, useMemo, useRef, useState } from "react";

import CardStackContainer from "@/components/shared/CardStackContainer";
import Composer from "@/features/chat/components/composer/Composer";
import { FileDropModal } from "@/features/chat/components/files/FileDropModal";
import ChatRenderer from "@/features/chat/components/interface/ChatRenderer";
import ScrollToBottomButton from "@/features/chat/components/interface/ScrollToBottomButton";
import ScrollForMoreButton from "@/features/chat/components/interface/ScrollForMoreButton";
import StarterText from "@/features/chat/components/interface/StarterText";
import { ComposerProvider } from "@/features/chat/contexts/ComposerContext";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useConversationList } from "@/features/chat/hooks/useConversationList";
import { fetchMessages } from "@/features/chat/utils/chatUtils";
import { filterEmptyMessagePairs } from "@/features/chat/utils/messageContentUtils";
import { useDragAndDrop } from "@/hooks/ui/useDragAndDrop";

const ChatPage = React.memo(function MainChat() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const { updateConvoMessages, convoMessages, clearMessages } =
    useConversation();
  const { conversations } = useConversationList();
  const { id: convoIdParam } = useParams<{ id: string }>();
  const messageId = searchParams.get("messageId");

  const chatRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const cardStackSectionRef = useRef<HTMLDivElement>(null);
  const dummySectionRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const [showScrollForMore, setShowScrollForMore] = useState(false);
  const [droppedFiles, setDroppedFiles] = useState<File[]>([]);
  const fileUploadRef = useRef<{
    openFileUploadModal: () => void;
    handleDroppedFiles: (files: File[]) => void;
  } | null>(null);

  const appendToInputRef = useRef<((text: string) => void) | null>(null);

  // Find the current conversation
  const conversation = useMemo(() => {
    return conversations.find(
      (convo) => convo.conversation_id === convoIdParam,
    );
  }, [conversations, convoIdParam]);

  // Check if there are any messages to determine layout
  const hasMessages = useMemo(() => {
    if (!convoMessages) return false;

    const filteredMessages = filterEmptyMessagePairs(
      convoMessages,
      conversation?.is_system_generated || false,
      conversation?.system_purpose,
    );

    return filteredMessages.length > 0;
  }, [
    convoMessages,
    conversation?.is_system_generated,
    conversation?.system_purpose,
  ]);

  // const handleScroll = debounce((event: React.UIEvent, threshold = 1) => {
  //   const { scrollTop, scrollHeight, clientHeight } =
  //     event.target as HTMLElement;
  //   setIsAtBottom(scrollHeight - scrollTop <= clientHeight + threshold);
  // }, 100);

  const scrollToBottom = () => {
    // If a specific message is being viewed, do not scroll to bottom, scroll to that message instead.
    // This is to prevent the chat from scrolling to the bottom when a user is redirected to a specific message.
    // Scrolling to message is handled in ChatRenderer.
    if (messageId) return;
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  const scrollToCardStack = () => {
    if (cardStackSectionRef.current) {
      cardStackSectionRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  };

  const scrollToDummySection = () => {
    if (dummySectionRef.current) {
      dummySectionRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  };

  const handleNewChatScroll = (event: React.UIEvent) => {
    const { scrollTop, clientHeight } = event.target as HTMLElement;
    const isInFirstSection = scrollTop < clientHeight * 0.8;
    
    // For new chat page, always show the button unless user has scrolled to second section
    setShowScrollForMore(isInFirstSection);
  };

  const handleScroll = (event: React.UIEvent) => {
    const { scrollTop, scrollHeight, clientHeight } =
      event.target as HTMLElement;
    const isInFirstSection = scrollTop < clientHeight * 0.8; // Show button when near end of first section

    // Show scroll for more button when user is in the first section and has scrolled down
    // but hasn't reached the second section yet
    setShowScrollForMore(hasMessages && isInFirstSection && scrollTop > 200);
  };

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

  // ! THIS DOESNT CAUSE AN INFINITE LOOP
  useEffect(() => {
    if (convoIdParam) {
      fetchMessages(convoIdParam, updateConvoMessages, router).then(() => {
        setTimeout(scrollToBottom, 500);
      });
    } else {
      // Clear messages when navigating to /c without an ID (new chat)
      clearMessages();
      if (pathname !== "/c") router.push("/c");
    }

    if (inputRef?.current) inputRef.current.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [convoIdParam]);

  // Show scroll for more button when messages are loaded
  useEffect(() => {
    if (hasMessages) {
      // Delay showing the button to allow for initial scroll
      const timer = setTimeout(() => {
        setShowScrollForMore(true);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      // For new chat page, always show the scroll button
      setShowScrollForMore(true);
    }
  }, [hasMessages]);

  // ! THIS CAUSES AN INFINITE LOOP
  // const fetchConvoMessages = useCallback(async () => {
  //   if (convoIdParam) {
  //     await fetchMessages(convoIdParam, updateConvoMessages, router);
  //     setTimeout(scrollToBottom, 500);
  //   } else if (pathname !== "/c") {
  //     router.push("/c");
  //   }

  //   if (inputRef?.current) inputRef.current.focus();
  // }, [convoIdParam, updateConvoMessages, router, pathname]);

  // useEffect(() => {
  //   fetchConvoMessages();
  // }, [fetchConvoMessages]);

  // useEffect(() => {
  //   return () => {
  //     handleScroll.cancel();
  //   };
  // }, [handleScroll]);

  // Common composer props to avoid repetition
  const composerProps = {
    inputRef,
    scrollToBottom,
    fileUploadRef,
    appendToInputRef,
    droppedFiles,
    onDroppedFilesProcessed: () => setDroppedFiles([]),
    hasMessages,
  };

  // Common drag container props
  const dragContainerClass = `relative flex w-full ${isDragging ? "bg-zinc-800/30" : ""}`;

  // Function to append text to input - provided to context
  const appendToInput = (text: string) => {
    // Call the function from Composer via ref
    if (appendToInputRef.current) {
      appendToInputRef.current(text);
    }
  };

  return (
    <ComposerProvider value={{ appendToInput }}>
      <div className="flex h-full flex-col">
        {hasMessages ? (
          // Layout with messages: Chat with scroll snapping sections
          <div
            ref={scrollContainerRef}
            className="h-full snap-y snap-mandatory overflow-y-auto scroll-smooth"
            onScroll={handleScroll}
            {...dragHandlers}
          >
            <FileDropModal isDragging={isDragging} />

            {/* First section: Chat interface */}
            <div className="relative flex h-screen min-h-screen snap-start flex-col">
              <div className="flex-1 overflow-y-auto">
                <div
                  ref={chatRef}
                  className="conversation_history mx-auto w-full max-w-(--breakpoint-lg) p-2 sm:p-4"
                >
                  <ChatRenderer />
                </div>
              </div>
              <div className="flex-shrink-0 pb-2">
                <Composer {...composerProps} />
              </div>
            </div>

            {/* Second section: Card Stack Container */}
            <div
              ref={cardStackSectionRef}
              className="relative flex h-screen min-h-screen snap-start items-center justify-center p-4"
            >
              <div className="w-full max-w-(--breakpoint-xl)">
                <CardStackContainer />
              </div>
            </div>

            {/* Scroll buttons */}
            <ScrollToBottomButton
              containerRef={scrollContainerRef}
              onScrollToBottom={scrollToBottom}
              threshold={150}
            />
            <ScrollForMoreButton
              onClick={scrollToCardStack}
              visible={showScrollForMore}
            />
          </div>
        ) : (
          // Layout without messages: Scroll snapping sections for new chat
          <div
            ref={scrollContainerRef}
            className="h-full snap-y snap-mandatory overflow-y-auto scroll-smooth"
            onScroll={handleNewChatScroll}
            {...dragHandlers}
          >
            <FileDropModal isDragging={isDragging} />
            
            {/* First section: New chat interface */}
            <div className="relative flex h-screen min-h-screen snap-start items-center justify-center p-4">
              <div className="flex w-full max-w-(--breakpoint-xl) flex-col items-center justify-center gap-10">
                <div className="flex flex-col items-center gap-2">
                  <Image
                    alt="GAIA Logo"
                    src="/branding/logo.webp"
                    width={110}
                    height={110}
                  />
                  <StarterText />
                </div>
                <div className="w-full">
                  <Composer {...composerProps} />
                </div>
                <CardStackContainer />
              </div>
            </div>

            {/* Second section: Dummy text section */}
            <div
              ref={dummySectionRef}
              className="relative flex h-screen min-h-screen snap-start items-center justify-center p-4"
            >
              <div className="text-center">
                <h1 className="text-4xl font-bold text-foreground">
                  DUMMY TEXT
                </h1>
                <p className="mt-4 text-lg text-foreground/60">
                  This is a placeholder section for additional content
                </p>
              </div>
            </div>

            {/* Scroll button for new chat */}
            <ScrollForMoreButton
              onClick={scrollToDummySection}
              visible={showScrollForMore}
            />
          </div>
        )}
      </div>
    </ComposerProvider>
  );
});

export default ChatPage;
