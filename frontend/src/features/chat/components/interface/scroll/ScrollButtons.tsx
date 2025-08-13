import React from "react";
import ScrollToBottomButton from "@/features/chat/components/interface/ScrollToBottomButton";

interface ScrollButtonsProps {
  containerRef: React.RefObject<HTMLDivElement | null>;
  onScrollToBottom: () => void;
  hasMessages: boolean;
}

export const ScrollButtons: React.FC<ScrollButtonsProps> = ({
  containerRef,
  onScrollToBottom,
  hasMessages,
}) => {
  return (
    <ScrollToBottomButton
      containerRef={containerRef}
      onScrollToBottom={onScrollToBottom}
      threshold={150}
      hasMessages={hasMessages}
    />
  );
};
