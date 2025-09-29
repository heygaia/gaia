import React from "react";

import Composer from "@/features/chat/components/composer/Composer";
import StarterText from "@/features/chat/components/interface/StarterText";

interface NewChatSectionProps {
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
  voiceModeActive: () => void;
}

export const NewChatSection: React.FC<NewChatSectionProps> = ({
  composerProps,
  voiceModeActive
}) => {
  return (
    <div className="relative flex w-full snap-start items-center justify-center p-4 pt-[25vh]">
      <div className="flex w-full max-w-(--breakpoint-xl) flex-col items-center justify-center gap-10">
        <div className="flex flex-col items-center gap-2">
          <StarterText />
        </div>
        <div className="w-full">
          <Composer {...composerProps} voiceModeActive={voiceModeActive} />
        </div>
        {/* <CardStackContainer /> */}
      </div>
    </div>
  );
};
