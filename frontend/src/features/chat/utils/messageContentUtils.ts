import { SystemPurpose } from "@/features/chat/api/chatApi";
import {
  BASE_MESSAGE_KEYS,
  BASE_MESSAGE_SCHEMA,
  BaseMessageData,
} from "@/types/features/baseMessageRegistry";
import { ChatBubbleBotProps } from "@/types/features/chatBubbleTypes";
import { ConversationMessage, MessageType } from "@/types/features/convoTypes";

/**
 * Check if text bubble should be shown (considering system-generated conversations)
 */
export const shouldShowTextBubble = (
  text: string,
  isConvoSystemGenerated?: boolean,
  systemPurpose?: SystemPurpose,
): boolean => {
  // Don't show text bubble when conversation is system generated for mail_processing
  const isEmailProcessingSystem =
    isConvoSystemGenerated && systemPurpose === SystemPurpose.EMAIL_PROCESSING;

  if (isEmailProcessingSystem) {
    return false;
  }

  return !!text.trim();
};

/**
 * Comprehensive check to determine if a bot message has any meaningful content
 */
export const isBotMessageEmpty = (props: ChatBubbleBotProps): boolean => {
  const { text, loading, isConvoSystemGenerated, systemPurpose } = props;

  if (loading) return false;

  // Only check keys that are in BASE_MESSAGE_KEYS
  const hasAnyContent = BASE_MESSAGE_KEYS.some((key) => !!props[key]);

  return !(
    hasAnyContent ||
    shouldShowTextBubble(text, isConvoSystemGenerated, systemPurpose)
  );
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

    if (currentMessage.type === "user" && i + 1 < messages.length) {
      const nextMessage = messages[i + 1];

      if (nextMessage.type === "bot") {
        // Build base fields from BASE_MESSAGE_KEYS
        const baseFields: BaseMessageData = Object.fromEntries(
          BASE_MESSAGE_KEYS.map((key) => [
            key,
            key in nextMessage
              ? (nextMessage as ConversationMessage)[key]
              : BASE_MESSAGE_SCHEMA[key],
          ]),
        ) as BaseMessageData;
        // Build the full botProps object
        const botProps: ChatBubbleBotProps = {
          ...baseFields,
          text: nextMessage.response || "",
          loading: nextMessage.loading,
          setOpenImage: () => {},
          setImageData: () => {},
          systemPurpose,
          isConvoSystemGenerated,
        };

        if (!isBotMessageEmpty(botProps)) {
          filteredMessages.push(currentMessage);
          filteredMessages.push(nextMessage);
        }
        i++;
      } else {
        filteredMessages.push(currentMessage);
      }
    } else if (currentMessage.type === "bot") {
      // Standalone bot message (not part of a pair)
      const baseFields: BaseMessageData = Object.fromEntries(
        BASE_MESSAGE_KEYS.map((key) => [
          key,
          key in currentMessage
            ? (currentMessage as ConversationMessage)[key]
            : BASE_MESSAGE_SCHEMA[key],
        ]),
      ) as BaseMessageData;
      const botProps: ChatBubbleBotProps = {
        ...baseFields,
        text: currentMessage.response || "",
        loading: currentMessage.loading,
        setOpenImage: () => {},
        setImageData: () => {},
        systemPurpose,
        isConvoSystemGenerated,
      };

      if (!isBotMessageEmpty(botProps)) {
        filteredMessages.push(currentMessage);
      }
    } else {
      filteredMessages.push(currentMessage);
    }
  }

  return filteredMessages;
};
