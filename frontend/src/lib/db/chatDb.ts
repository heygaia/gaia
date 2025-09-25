import Dexie, { Table } from "dexie";

import { SystemPurpose } from "@/features/chat/api/chatApi";
import { FileData } from "@/types/shared";

type MessageRole = "user" | "assistant" | "system";
type MessageStatus = "sending" | "sent" | "failed";

export interface IConversation {
  id: string;
  title: string;
  description?: string;
  userId?: string;
  starred?: boolean;
  isSystemGenerated?: boolean;
  systemPurpose?: SystemPurpose | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface IMessage {
  id: string;
  conversationId: string;
  content: string;
  role: MessageRole;
  status?: MessageStatus;
  createdAt: Date;
  updatedAt?: Date;
  messageId?: string;
  fileIds?: string[];
  fileData?: FileData[];
  toolName?: string | null;
  toolCategory?: string | null;
  workflowId?: string | null;
  metadata?: Record<string, unknown>;
}

export class ChatDexie extends Dexie {
  public conversations!: Table<IConversation, string>;
  public messages!: Table<IMessage, string>;

  constructor() {
    super("ChatDatabase");

    this.version(1).stores({
      conversations: "id, updatedAt, createdAt",
      messages: "id, conversationId, createdAt",
    });

    this.conversations = this.table("conversations");
    this.messages = this.table("messages");
  }

  public getConversation(id: string): Promise<IConversation | undefined> {
    return this.conversations.get(id);
  }

  public getAllConversations(): Promise<IConversation[]> {
    return this.conversations.orderBy("updatedAt").reverse().toArray();
  }

  public async putConversation(conversation: IConversation): Promise<string> {
    return this.conversations.put(conversation);
  }

  public async putConversationsBulk(
    conversations: IConversation[],
  ): Promise<string[]> {
    await this.conversations.bulkPut(conversations);
    return conversations.map((conversation) => conversation.id);
  }

  public getMessagesForConversation(
    conversationId: string,
  ): Promise<IMessage[]> {
    return this.messages
      .where("conversationId")
      .equals(conversationId)
      .sortBy("createdAt");
  }

  public putMessage(message: IMessage): Promise<string> {
    return this.messages.put(message);
  }

  public async putMessagesBulk(messages: IMessage[]): Promise<string[]> {
    await this.messages.bulkPut(messages);
    return messages.map((message) => message.id);
  }

  public async deleteConversationAndMessages(
    conversationId: string,
  ): Promise<void> {
    await this.transaction(
      "rw",
      this.conversations,
      this.messages,
      async () => {
        await this.messages
          .where("conversationId")
          .equals(conversationId)
          .delete();
        await this.conversations.delete(conversationId);
      },
    );
  }
}

export const db = new ChatDexie();
