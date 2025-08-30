import React from "react";

import Composer from "@/features/chat/components/composer/Composer";

import { ChatSection } from "../sections";

interface ChatWithMessagesProps {
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  chatRef: React.RefObject<HTMLDivElement | null>;
  handleScroll: (event: React.UIEvent) => void;
  dragHandlers: {
    onDragEnter: (e: React.DragEvent<HTMLElement>) => void;
    onDragOver: (e: React.DragEvent<HTMLElement>) => void;
    onDragLeave: (e: React.DragEvent<HTMLElement>) => void;
    onDrop: (e: React.DragEvent<HTMLElement>) => void;
  };
  composerProps: {
    inputRef: React.RefObject<HTMLTextAreaElement | null>;
    scrollToBottom: () => void;
    fileUploadRef: React.RefObject<{
      openFileUploadModal: () => void;
      handleDroppedFiles: (files: File[]) => void;
    } | null>;
    droppedFiles: File[];
    onDroppedFilesProcessed: () => void;
    hasMessages: boolean;
  };
}

export const ChatWithMessages: React.FC<ChatWithMessagesProps> = ({
  scrollContainerRef,
  chatRef,
  handleScroll,
  dragHandlers,
  composerProps,
}) => {
  return (
    <div
      ref={scrollContainerRef}
      className="h-full overflow-y-auto"
      onScroll={handleScroll}
      {...dragHandlers}
    >
      {/* Chat interface - no snap scrolling when there are messages */}
      <div className="relative flex h-full flex-col">
        <ChatSection chatRef={chatRef} />
        <div className="flex-shrink-0 pb-2">
          <Composer {...composerProps} />
        </div>
      </div>
    </div>
  );
};
