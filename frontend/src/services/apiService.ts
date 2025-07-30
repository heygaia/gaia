import {
  EventSourceMessage,
  fetchEventSource,
} from "@microsoft/fetch-event-source";

import { chatApi } from "@/features/chat/api/chatApi";
import { MessageType } from "@/types/features/convoTypes";
import { FileData } from "@/types/shared";

export const ApiService = {
  fetchMessages: async (conversationId: string) => {
    if (!conversationId) return;
    try {
      return await chatApi.fetchMessages(conversationId);
    } catch (error) {
      console.error(
        `Error fetching messages for conversation ${conversationId}:`,
        error,
      );
      throw error;
    }
  },

  deleteAllConversations: async () => {
    try {
      await chatApi.deleteAllConversations();
    } catch (error) {
      console.error("Error deleting all conversations:", error);
      throw error;
    }
  },

  fetchChatStream: async (
    inputText: string,
    convoMessages: MessageType[],
    conversationId: string | null,
    onMessage: (event: EventSourceMessage) => void,
    onClose: () => void,
    onError: (err: Error) => void,
    fileData: FileData[] = [], // Updated to accept FileData instead of fileIds
  ) => {
    const controller = new AbortController();

    // Extract fileIds from fileData for backward compatibility
    const fileIds = fileData.map((file) => file.fileId);

    await fetchEventSource(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}chat-stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          "x-timezone": Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
        credentials: "include",
        signal: controller.signal,
        body: JSON.stringify({
          conversation_id: conversationId,
          message: inputText,
          fileIds, // For backward compatibility
          fileData, // Send complete file data
          messages: convoMessages
            .slice(-30)
            .filter(({ response }) => response.trim().length > 0)
            .map(({ type, response }, _index, _array) => ({
              role: type === "bot" ? "assistant" : type,
              content: response,
            })),
        }),
        onmessage(event) {
          onMessage(event);

          if (event.data === "[DONE]") {
            onClose();
            controller.abort();
            return;
          }
        },
        onclose() {
          onClose();
          controller.abort();
        },
        onerror: onError,
      },
    );
  },
};
