import { useCallback } from "react";

import { chatApi } from "@/features/chat/api/chatApi";
import {
  ConversationPaginationMeta,
  useConversationsStore,
} from "@/stores/conversationsStore";
import { putConversationsBulk } from "@/services/indexedDb/chatDb";

export const useConversationsOperations = () => {
  const {
    setConversations,
    setPaginationMeta,
    setLoading,
    setError,
    clearError,
  } = useConversationsStore();

  const fetchConversations = useCallback(
    async (page = 1, limit = 20, append = true) => {
      setLoading(true);
      clearError();

      try {
        const data = await chatApi.fetchConversations(page, limit);

        const conversations = data.conversations ?? [];
        const paginationMeta: ConversationPaginationMeta = {
          total: data.total ?? 0,
          page: data.page ?? 1,
          limit: data.limit ?? limit,
          total_pages: data.total_pages ?? 1,
        };

        setConversations(conversations, append);
        setPaginationMeta(paginationMeta);

        // Persist server-fetched conversations into IndexedDB in background
        try {
          if (conversations && conversations.length > 0) {
            putConversationsBulk(conversations as any).catch((e) =>
              console.error("putConversationsBulk error:", e),
            );
          }
        } catch (e) {
          console.error("Error persisting conversations to IndexedDB:", e);
        }

        return { conversations, paginationMeta };
      } catch (error) {
        const errorMessage =
          error instanceof Error
            ? error.message
            : "Failed to fetch conversations";
        setError(errorMessage);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [setConversations, setPaginationMeta, setLoading, setError, clearError],
  );

  return {
    fetchConversations,
  };
};
