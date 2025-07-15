import { SystemPurpose } from "@/features/chat/api/chatApi";
import { ChatBubbleBotProps } from "@/types/features/chatBubbleTypes";
import { MessageType } from "@/types/features/convoTypes";

/**
 * Check if text bubble should be shown (considering system-generated conversations)
 */
export const shouldShowTextBubble = (
  text: string,
  searchWeb?: boolean,
  deepSearchWeb?: boolean,
  pageFetchURLs?: string[],
  isConvoSystemGenerated?: boolean,
  systemPurpose?: SystemPurpose,
): boolean => {
  // Don't show text bubble when conversation is system generated for mail_processing
  const isEmailProcessingSystem =
    isConvoSystemGenerated && systemPurpose === SystemPurpose.EMAIL_PROCESSING;

  if (isEmailProcessingSystem) {
    return false;
  }

  return (
    !!searchWeb ||
    !!deepSearchWeb ||
    (!!pageFetchURLs && pageFetchURLs.length > 0) ||
    !!text.trim()
  );
};

/**
 * Comprehensive check to determine if a bot message has any meaningful content
 */
export const isBotMessageEmpty = (props: ChatBubbleBotProps): boolean => {
  const {
    text,
    loading,
    searchWeb,
    deepSearchWeb,
    pageFetchURLs,
    disclaimer,
    calendar_options,
    calendar_delete_options,
    calendar_edit_options,
    email_compose_data,
    email_fetch_data,
    weather_data,
    todo_data,
    goal_data,
    code_data,
    search_results,
    deep_research_results,
    document_data,
    google_docs_data,
    image_data,
    memory_data,
    isConvoSystemGenerated,
    systemPurpose,
  } = props;

  // If the message is currently loading, it should never be considered empty
  // This ensures streaming messages remain visible during the streaming process
  if (loading) return false;

  // Check all possible content types
  const hasAnyContent =
    !!search_results ||
    !!deep_research_results ||
    !!weather_data ||
    shouldShowTextBubble(
      text,
      searchWeb,
      deepSearchWeb,
      pageFetchURLs,
      isConvoSystemGenerated,
      systemPurpose,
    ) ||
    !!calendar_options ||
    !!calendar_delete_options ||
    !!calendar_edit_options ||
    !!email_compose_data ||
    !!todo_data ||
    !!document_data ||
    !!google_docs_data ||
    !!goal_data ||
    !!code_data ||
    !!image_data ||
    !!memory_data;

  return !hasAnyContent;
};

/**
 * Filter out empty message pairs from a conversation
 * This will remove user+bot message pairs where the bot response is completely empty
 */
export const filterEmptyMessagePairs = (
  messages: MessageType[],
  isConvoSystemGenerated: boolean = false,
  systemPurpose?: SystemPurpose,
): MessageType[] => {
  const filteredMessages: MessageType[] = [];

  for (let i = 0; i < messages.length; i++) {
    const currentMessage = messages[i];

    // If this is a user message, check if the next message (bot response) is empty
    if (currentMessage.type === "user" && i + 1 < messages.length) {
      const nextMessage = messages[i + 1];

      if (nextMessage.type === "bot") {
        // Create bot props with conversation context
        const botProps: ChatBubbleBotProps = {
          message_id: nextMessage.message_id || "",
          text: nextMessage.response || "",
          loading: nextMessage.loading,
          searchWeb: nextMessage.searchWeb,
          deepSearchWeb: nextMessage.deepSearchWeb,
          disclaimer: nextMessage.disclaimer,
          date: nextMessage.date,
          setOpenImage: () => {}, // Mock function
          setImageData: () => {}, // Mock function
          pageFetchURLs: nextMessage.pageFetchURLs,
          pinned: nextMessage.pinned,
          calendar_options: nextMessage.calendar_options,
          calendar_delete_options: nextMessage.calendar_delete_options,
          calendar_edit_options: nextMessage.calendar_edit_options,
          email_compose_data: nextMessage.email_compose_data,
          email_fetch_data: nextMessage.email_fetch_data,
          weather_data: nextMessage.weather_data,
          search_results: nextMessage.search_results,
          deep_research_results: nextMessage.deep_research_results,
          document_data: nextMessage.document_data,
          image_data: nextMessage.image_data,
          todo_data: nextMessage.todo_data,
          code_data: nextMessage.code_data,
          memory_data: nextMessage.memory_data,
          goal_data: nextMessage.goal_data,
          google_docs_data: nextMessage.google_docs_data,
          isConvoSystemGenerated,
          systemPurpose,
        };

        // If the bot message is not empty, include both user and bot messages
        if (!isBotMessageEmpty(botProps)) {
          filteredMessages.push(currentMessage);
          filteredMessages.push(nextMessage);
        }
        // If bot message is empty, skip both messages (don't add them to filtered)

        // Skip the next iteration since we've already processed the bot message
        i++;
      } else {
        // If next message is not a bot message, include the current user message
        filteredMessages.push(currentMessage);
      }
    } else if (currentMessage.type === "bot") {
      // Standalone bot message (not part of a pair)
      const botProps: ChatBubbleBotProps = {
        message_id: currentMessage.message_id || "",
        text: currentMessage.response || "",
        loading: currentMessage.loading,
        searchWeb: currentMessage.searchWeb,
        deepSearchWeb: currentMessage.deepSearchWeb,
        disclaimer: currentMessage.disclaimer,
        date: currentMessage.date,
        setOpenImage: () => {}, // Mock function
        setImageData: () => {}, // Mock function
        pageFetchURLs: currentMessage.pageFetchURLs,
        pinned: currentMessage.pinned,
        calendar_options: currentMessage.calendar_options,
        calendar_delete_options: currentMessage.calendar_delete_options,
        calendar_edit_options: currentMessage.calendar_edit_options,
        email_compose_data: currentMessage.email_compose_data,
        email_fetch_data: currentMessage.email_fetch_data,
        weather_data: currentMessage.weather_data,
        search_results: currentMessage.search_results,
        deep_research_results: currentMessage.deep_research_results,
        document_data: currentMessage.document_data,
        image_data: currentMessage.image_data,
        todo_data: currentMessage.todo_data,
        code_data: currentMessage.code_data,
        memory_data: currentMessage.memory_data,
        goal_data: currentMessage.goal_data,
        google_docs_data: currentMessage.google_docs_data,
        isConvoSystemGenerated,
        systemPurpose,
      };

      // Only include if not empty
      if (!isBotMessageEmpty(botProps)) {
        filteredMessages.push(currentMessage);
      }
    } else {
      // Standalone user message
      filteredMessages.push(currentMessage);
    }
  }

  return filteredMessages;
};
