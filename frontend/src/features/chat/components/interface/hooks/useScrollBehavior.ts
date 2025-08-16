import { useCallback, useRef } from "react";

interface UseScrollBehaviorReturn {
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  scrollToBottom: () => void;
  handleScroll: (event: React.UIEvent) => void;
  handleNewChatScroll: (event: React.UIEvent) => void;
}

export const useScrollBehavior = (
  hasMessages: boolean,
  messageId: string | null,
): UseScrollBehaviorReturn => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    // If a specific message is being viewed, do not scroll to bottom
    if (messageId) return;
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messageId]);

  const handleNewChatScroll = useCallback((_event: React.UIEvent) => {
    // Simple scroll handler for new chat - no special logic needed
  }, []);

  const handleScroll = useCallback(
    (_event: React.UIEvent) => {
      // Simple scroll handler for chat messages - no special logic needed
    },
    [hasMessages],
  );

  return {
    scrollContainerRef,
    scrollToBottom,
    handleScroll,
    handleNewChatScroll,
  };
};
