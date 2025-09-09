import { useCallback } from "react";

import type { Conversation as ApiConversation } from "@/features/chat/api/chatApi";
import type { MessageType } from "@/types/features/convoTypes";
import {
  getAllConversations,
  getMessagesForConversation,
  putConversationsBulk,
  // putMessagesBulk,
  putMessage,
  putMessagesBulk as _putMessagesBulk,
} from "@/services/indexedDb/chatDb";

export const useChatDb = () => {
  const loadConversations = useCallback(async () => {
    return await getAllConversations();
  }, []);

  const saveConversations = useCallback(async (conversations: ApiConversation[]) => {
    // Cast to ConversationRecord is handled inside putConversationsBulk
    await putConversationsBulk(conversations as any);
  }, []);

  const loadMessages = useCallback(async (conversationId: string) => {
    return await getMessagesForConversation(conversationId);
  }, []);

  const saveMessages = useCallback(async (messages: MessageType[]) => {
    await _putMessagesBulk(messages as any);
  }, []);

  const saveMessage = useCallback(async (message: MessageType) => {
    await putMessage(message as any);
  }, []);

  return {
    loadConversations,
    saveConversations,
    loadMessages,
    saveMessages,
    saveMessage,
  } as const;
};

export default useChatDb;
