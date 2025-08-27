import { create } from "zustand";

import { chatApi, type Conversation } from "@/features/chat/api/chatApi";

export type { Conversation };

export interface ConversationPaginationMeta {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface ConversationsState {
  conversations: Conversation[];
  paginationMeta: ConversationPaginationMeta | null;
  loading: boolean;
  error: string | null;
  setConversations: (conversations: Conversation[]) => void;
  clearConversations: () => void;
  fetchConversations: (params?: {
    page?: number;
    limit?: number;
    append?: boolean;
  }) => Promise<void>;
}

export const useConversationsStore = create<ConversationsState>(
  (set, _get) => ({
    conversations: [],
    paginationMeta: null,
    loading: false,
    error: null,

    setConversations: (conversations: Conversation[]) => set({ conversations }),

    clearConversations: () =>
      set({
        conversations: [],
        paginationMeta: null,
      }),

    fetchConversations: async ({
      page = 1,
      limit = 20,
      append = true,
    } = {}) => {
      set({ loading: true, error: null });

      try {
        const data = await chatApi.fetchConversations(page, limit);
        const conversations = data.conversations ?? [];
        const paginationMeta = {
          total: data.total ?? 0,
          page: data.page ?? 1,
          limit: data.limit ?? limit,
          total_pages: data.total_pages ?? 1,
        };

        set((state) => {
          let updatedConversations;
          if (append) {
            const combined = [...state.conversations, ...conversations];
            const uniqueMap = new Map(
              combined.map((conv) => [conv.conversation_id, conv]),
            );
            updatedConversations = Array.from(uniqueMap.values());
          } else {
            updatedConversations = conversations;
          }

          return {
            conversations: updatedConversations,
            paginationMeta,
            loading: false,
          };
        });
      } catch (error) {
        set({
          loading: false,
          error: (error as Error).message || "Failed to fetch conversations",
        });
      }
    },
  }),
);
