import React from "react";

import { UseDragAndDropReturn } from "@/hooks/ui/useDragAndDrop";

import { GridSection, NewChatSection } from "../sections";

interface NewChatLayoutProps {
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  dummySectionRef: React.RefObject<HTMLDivElement | null>;
  handleNewChatScroll: (event: React.UIEvent) => void;
  dragHandlers: UseDragAndDropReturn["dragHandlers"];
  composerProps: {
    inputRef: React.RefObject<HTMLTextAreaElement | null>;
    scrollToBottom: () => void;
    fileUploadRef: React.RefObject<{
      openFileUploadModal: () => void;
      handleDroppedFiles: (files: File[]) => void;
    } | null>;
    appendToInputRef: React.RefObject<((text: string) => void) | null>;
    droppedFiles: File[];
    onDroppedFilesProcessed: () => void;
    hasMessages: boolean;
  };
}

export const NewChatLayout: React.FC<NewChatLayoutProps> = ({
  scrollContainerRef,
  dummySectionRef,
  handleNewChatScroll,
  dragHandlers,
  composerProps,
}) => {
  return (
    <div
      ref={scrollContainerRef}
      className="h-full snap-y snap-mandatory overflow-y-auto scroll-smooth"
      onScroll={handleNewChatScroll}
      {...dragHandlers}
    >
      {/* First section: New chat interface */}
      <NewChatSection composerProps={composerProps} />

      {/* Second section: 2x2 Grid layout */}
      <GridSection dummySectionRef={dummySectionRef} />
    </div>
  );
};
