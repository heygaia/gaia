import React from "react";

import UseCaseSection from "@/features/use-cases/components/UseCaseSection";

import { GridSection, NewChatSection } from "../sections";

interface NewChatLayoutProps {
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  dummySectionRef: React.RefObject<HTMLDivElement | null>;
  handleNewChatScroll: (event: React.UIEvent) => void;
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
      className="h-full space-y-20 overflow-y-auto"
      onScroll={handleNewChatScroll}
      {...dragHandlers}
    >
      <div className="flex w-full flex-col items-center px-4">
        <NewChatSection composerProps={composerProps} />
        <UseCaseSection dummySectionRef={dummySectionRef} />
      </div>
      <GridSection />
    </div>
  );
};
