import { chatApi } from "@/features/chat/api/chatApi";
import { db, type IMessage } from "@/lib/db/chatDb";
import { MessageType } from "@/types/features/convoTypes";

const PAGE_SIZE = 50;

type ConversationSummary = {
  conversation_id: string;
};

const mapApiMessagesToStored = (
  messages: MessageType[],
  conversationId: string,
): IMessage[] =>
  messages.map((message, index) => {
    const createdAt = message.date ? new Date(message.date) : new Date();
    const role = mapMessageRole(message.type);
    const messageId =
      message.message_id || `${conversationId}-${index}-${createdAt.getTime()}`;

    return {
      id: messageId,
      conversationId,
      content: message.response,
      role,
      status: message.loading ? "sending" : "sent",
      createdAt,
      updatedAt: createdAt,
      messageId: message.message_id,
      fileIds: message.fileIds,
      fileData: message.fileData,
      toolName: message.selectedTool ?? null,
      toolCategory: message.toolCategory ?? null,
      workflowId: message.selectedWorkflow?.id ?? null,
      metadata: {
        originalMessage: message,
      },
    } satisfies IMessage;
  });

const mapMessageRole = (
  role: MessageType["type"],
): "user" | "assistant" | "system" => {
  switch (role) {
    case "user":
      return "user";
    case "bot":
      return "assistant";
    default:
      return "system";
  }
};

const fetchAllConversationIds = async (): Promise<string[]> => {
  let page = 1;
  let totalPages = 1;
  const conversationIds: string[] = [];

  while (page <= totalPages) {
    try {
      const response = await chatApi.fetchConversations(page, PAGE_SIZE);
      totalPages = response.total_pages ?? 1;
      conversationIds.push(
        ...response.conversations
          .map((conversation: ConversationSummary) => conversation.conversation_id)
          .filter((id): id is string => Boolean(id)),
      );
      page += 1;
    } catch {
      break;
    }
  }

  return Array.from(new Set(conversationIds));
};

export const syncAndPrecacheMessages = async (): Promise<void> => {
  try {
    const [remoteConversationIds, cachedConversationIds] = await Promise.all([
      fetchAllConversationIds(),
      db.getConversationIdsWithMessages(),
    ]);

    if (remoteConversationIds.length === 0) {
      return;
    }

    const cachedSet = new Set(cachedConversationIds);
    const pendingConversationIds = remoteConversationIds.filter(
      (conversationId) => !cachedSet.has(conversationId),
    );

    for (const conversationId of pendingConversationIds) {
      try {
        const messages = await chatApi.fetchMessages(conversationId);
        if (messages.length === 0) continue;

        const mappedMessages = mapApiMessagesToStored(
          messages,
          conversationId,
        );

        if (mappedMessages.length === 0) continue;

        await db.putMessagesBulk(mappedMessages);
      } catch {
        continue;
      }
    }
  } catch {
    // Ignore background sync errors to avoid impacting the UI
  }
};
