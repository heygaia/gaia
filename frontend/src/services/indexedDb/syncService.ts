import { chatApi } from "@/features/chat/api/chatApi";
import { putConversationsBulk, putMessagesBulk } from "@/services/indexedDb/chatDb";
import type { Conversation } from "@/features/chat/api/chatApi";

/**
 * Simple sync service: fetch from backend and persist results into IndexedDB.
 * Callers should also dispatch to Redux if they want immediate UI updates.
 */
export const syncConversationsToDb = async (page = 1, limit = 50) => {
  try {
    const data = await chatApi.fetchConversations(page, limit);
    const conversations: Conversation[] = data.conversations ?? [];
    if (conversations.length > 0) await putConversationsBulk(conversations as any);
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
    if (messages && messages.length > 0) await putMessagesBulk(messages as any);
    return messages;
  } catch (err) {
    console.error("syncMessagesForConversation error:", err);
    return [];
  }
};

export default {
  syncConversationsToDb,
  syncMessagesForConversation,
};
