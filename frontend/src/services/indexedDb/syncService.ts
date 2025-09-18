import type { Conversation } from "@/features/chat/api/chatApi";
import { chatApi } from "@/features/chat/api/chatApi";
import {
  putConversationsBulk,
  putMessagesBulk,
} from "@/services/indexedDb/chatDb";

/**
 * Simple sync service: fetch from backend and persist results into IndexedDB.
 * Callers should also dispatch to Redux if they want immediate UI updates.
 */
export const syncConversationsToDb = async (page = 1, limit = 50) => {
  try {
    const data = await chatApi.fetchConversations(page, limit);
    const conversations: Conversation[] = (data.conversations ??
      []) as Conversation[];
    if (conversations.length > 0)
      await putConversationsBulk(
        conversations as import("@/services/indexedDb/chatDb").ConversationRecord[],
      );
    return conversations;
  } catch (err) {
    console.error("syncConversationsToDb error:", err);
    return [];
  }
};

export const syncMessagesForConversation = async (conversationId: string) => {
  try {
    if (!conversationId) return [];
    const messages = await chatApi.fetchMessages(conversationId);
    if (messages && messages.length > 0)
      await putMessagesBulk(
        messages as import("@/types/features/convoTypes").MessageType[],
      );
    return messages;
  } catch (err) {
    console.error("syncMessagesForConversation error:", err);
    return [];
  }
};

export const syncService = {
  syncConversationsToDb,
  syncMessagesForConversation,
};

export default syncService;
