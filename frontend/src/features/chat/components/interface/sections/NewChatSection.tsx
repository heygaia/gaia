import Image from "next/image";
import React from "react";

import CardStackContainer from "@/components/shared/CardStackContainer";
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
}

export const NewChatSection: React.FC<NewChatSectionProps> = ({
  composerProps,
}) => {
  return (
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
  );
};
