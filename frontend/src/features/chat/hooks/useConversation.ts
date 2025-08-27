import { useConversationStore } from "@/stores/conversationStore";
import { MessageType } from "@/types/features/convoTypes";

export const useConversation = () => {
  const {
    messages: convoMessages,
    setMessages,
    resetMessages,
  } = useConversationStore();

  const updateConvoMessages = (
    updater: MessageType[] | ((oldMessages: MessageType[]) => MessageType[]),
  ): void => {
    const newMessages =
      typeof updater === "function" ? updater(convoMessages) : updater;
    setMessages(newMessages);
  };

  const clearMessages = (): void => {
    resetMessages();
  };

  return {
    convoMessages,
    updateConvoMessages,
    clearMessages,
  };
};
