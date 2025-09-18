import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";
import { Dispatch, SetStateAction } from "react";

import { chatApi } from "@/features/chat/api/chatApi";
import {
  getMessagesForConversation,
  putMessagesBulk,
} from "@/services/indexedDb/chatDb";
import { MessageType } from "@/types/features/convoTypes";

export const fetchMessages = async (
  conversationId: string,
  setConvoMessages: Dispatch<SetStateAction<MessageType[]>>,
  router: AppRouterInstance | string[],
) => {
  try {
    if (!conversationId) return;

    // Fast-path: load from IndexedDB first
    try {
      const local = await getMessagesForConversation(conversationId);
      if (local && local.length > 0) {
        setConvoMessages(local as MessageType[]);
      }
    } catch (dbErr) {
      console.error("Failed to read messages from IndexedDB:", dbErr);
    }

    // Then fetch authoritative messages from the server
    const messages = await chatApi.fetchMessages(conversationId);

    if (messages && messages.length > 0) {
      setConvoMessages(messages);
      // Persist into IndexedDB (background)
      putMessagesBulk(messages).catch((e) =>
        console.error("putMessagesBulk error:", e),
      );
    }
  } catch (e) {
    console.error("Failed to fetch messages:", e);
    router.push("/c");
  }
};

/**
 * Format tool name for display
 * Converts snake_case tool names to readable format
 */
export const formatToolName = (toolName: string): string => {
  return toolName
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .replace(/Tool$/, "")
    .trim();
};
