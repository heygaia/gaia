import { create } from "zustand";
import { devtools } from "zustand/middleware";

import { Conversation } from "@/features/chat/api/chatApi";

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
}

interface ConversationsActions {
  setConversations: (conversations: Conversation[], append?: boolean) => void;
  setPaginationMeta: (meta: ConversationPaginationMeta) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearConversations: () => void;
  clearError: () => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (
    conversationId: string,
    updates: Partial<Conversation>,
  ) => void;
  removeConversation: (conversationId: string) => void;
}

type ConversationsStore = ConversationsState & ConversationsActions;

const initialState: ConversationsState = {
  conversations: [],
  paginationMeta: null,
  loading: false,
  error: null,
};

export const useConversationsStore = create<ConversationsStore>()(
  devtools(
    (set) => ({
      ...initialState,

      setConversations: (conversations, append = false) =>
        set(
          (state) => {
            if (append) {
              // Merge and deduplicate
              const combined = [...state.conversations, ...conversations];
              const uniqueMap = new Map(
                combined.map((conv) => [conv.conversation_id, conv]),
              );
              return { conversations: Array.from(uniqueMap.values()) };
            }
            return { conversations };
          },
          false,
          "setConversations",
        ),

      setPaginationMeta: (paginationMeta) =>
        set({ paginationMeta }, false, "setPaginationMeta"),

      setLoading: (loading) => set({ loading }, false, "setLoading"),

      setError: (error) => set({ error }, false, "setError"),

      clearConversations: () =>
        set(
          {
            conversations: [],
            paginationMeta: null,
          },
          false,
          "clearConversations",
        ),

      clearError: () => set({ error: null }, false, "clearError"),

      addConversation: (conversation) =>
        set(
          (state) => ({
            conversations: [conversation, ...state.conversations],
          }),
          false,
          "addConversation",
        ),

      updateConversation: (conversationId, updates) =>
        set(
          (state) => ({
            conversations: state.conversations.map((conv) =>
              conv.conversation_id === conversationId
                ? { ...conv, ...updates }
                : conv,
            ),
          }),
          false,
          "updateConversation",
        ),

      removeConversation: (conversationId) =>
        set(
          (state) => ({
            conversations: state.conversations.filter(
              (conv) => conv.conversation_id !== conversationId,
            ),
          }),
          false,
          "removeConversation",
        ),
    }),
    { name: "conversations-store" },
  ),
);

// Selectors
export const useConversations = () =>
  useConversationsStore((state) => state.conversations);
export const useConversationsPagination = () =>
  useConversationsStore((state) => state.paginationMeta);
export const useConversationsLoading = () =>
  useConversationsStore((state) => state.loading);
export const useConversationsError = () =>
  useConversationsStore((state) => state.error);
