import Dexie, { Table } from "dexie";

import type { Conversation as ApiConversation } from "@/features/chat/api/chatApi";
import type { MessageType } from "@/types/features/convoTypes";

export interface ConversationRecord extends ApiConversation {
  conversation_id: string;
}

export interface MessageRecord extends MessageType {
  message_id: string;
  conversation_id: string;
  date: string;
}

class ChatDB extends Dexie {
  conversations!: Table<ConversationRecord, string>;
  messages!: Table<MessageRecord, string>;

  constructor() {
    super("gaia_chat_db");

    // Schema v1: conversations and messages
    this.version(1).stores({
      conversations: "conversation_id,updatedAt,createdAt,starred",
      messages: "message_id,conversation_id,date",
    });

    // Example migration block for future schema changes
    // this.version(2).stores({
    //   conversations: "conversation_id,updatedAt,createdAt,starred,participants",
    //   messages: "message_id,conversation_id,date,serverSyncedAt"
    // }).upgrade(tx => {
    //   // migration logic
    // });
  }
}

export const chatDb = new ChatDB();

// Conversation helpers
export async function getAllConversations(): Promise<ConversationRecord[]> {
  try {
    return await chatDb.conversations.toArray();
  } catch (err) {
    console.error("chatDb.getAllConversations error:", err);
    return [];
  }
}

export async function putConversationsBulk(
  conversations: ConversationRecord[],
) {
  try {
    if (!conversations || conversations.length === 0) return;
    await chatDb.conversations.bulkPut(conversations as ConversationRecord[]);
  } catch (err) {
    console.error("chatDb.putConversationsBulk error:", err);
  }
}

export async function deleteConversation(conversationId: string) {
  try {
    await chatDb.conversations.delete(conversationId);
    await chatDb.messages
      .where("conversation_id")
      .equals(conversationId)
      .delete();
  } catch (err) {
    console.error("chatDb.deleteConversation error:", err);
  }
}

// Message helpers
export async function getMessagesForConversation(
  conversationId: string,
): Promise<MessageRecord[]> {
  try {
    return await chatDb.messages
      .where("conversation_id")
      .equals(conversationId)
      .sortBy("date");
  } catch (err) {
    console.error("chatDb.getMessagesForConversation error:", err);
    return [];
  }
}

function ensureString(v: unknown): string {
  return typeof v === "string" ? v : "";
}

export async function putMessagesBulk(
  messages: MessageType[] | MessageRecord[],
) {
  try {
    if (!messages || messages.length === 0) return;
    const normalized = (messages as MessageType[]).map((m) => {
      const mAny = m as unknown as Record<string, unknown>;
      return {
        message_id: ensureString(mAny["message_id"]) || "",
        conversation_id: ensureString(mAny["conversation_id"]) || "",
        date: ensureString(mAny["date"]) || new Date().toISOString(),
        ...(m as unknown as Record<string, unknown>),
      } as MessageRecord;
    });
    await chatDb.messages.bulkPut(normalized);
  } catch (err) {
    console.error("chatDb.putMessagesBulk error:", err);
  }
}

export async function putMessage(message: MessageType | MessageRecord) {
  try {
    const mAny = message as unknown as Record<string, unknown>;
    const normalized: MessageRecord = {
      message_id: ensureString(mAny["message_id"]) || "",
      conversation_id: ensureString(mAny["conversation_id"]) || "",
      date: ensureString(mAny["date"]) || new Date().toISOString(),
      ...(message as unknown as Record<string, unknown>),
    } as MessageRecord;
    await chatDb.messages.put(normalized);
  } catch (err) {
    console.error("chatDb.putMessage error:", err);
  }
}

export async function clearMessagesForConversation(conversationId: string) {
  try {
    await chatDb.messages
      .where("conversation_id")
      .equals(conversationId)
      .delete();
  } catch (err) {
    console.error("chatDb.clearMessagesForConversation error:", err);
  }
}

export async function clearAllConversations() {
  try {
    await chatDb.messages.clear();
    await chatDb.conversations.clear();
  } catch (err) {
    console.error("chatDb.clearAllConversations error:", err);
  }
}

export default chatDb;
