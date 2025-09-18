import { useCallback } from "react";

import type { Conversation as ApiConversation } from "@/features/chat/api/chatApi";
import type {
  ConversationRecord,
  MessageRecord,
} from "@/services/indexedDb/chatDb";
import {
  getAllConversations,
  getMessagesForConversation,
  putConversationsBulk,
  // putMessagesBulk,
  putMessage,
  putMessagesBulk as _putMessagesBulk,
} from "@/services/indexedDb/chatDb";
import type { MessageType } from "@/types/features/convoTypes";

export const useChatDb = () => {
  const loadConversations = useCallback(async () => {
    return await getAllConversations();
  }, []);

  const saveConversations = useCallback(
    async (conversations: ApiConversation[]) => {
      // Cast to ConversationRecord is handled inside putConversationsBulk
      await putConversationsBulk(
        conversations as unknown as ConversationRecord[],
      );
    },
    [],
  );

  const loadMessages = useCallback(async (conversationId: string) => {
    return await getMessagesForConversation(conversationId);
  }, []);

  const saveMessages = useCallback(async (messages: MessageType[]) => {
    await _putMessagesBulk(messages as unknown as MessageRecord[]);
  }, []);

  const saveMessage = useCallback(async (message: MessageType) => {
    await putMessage(message as unknown as MessageRecord);
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
