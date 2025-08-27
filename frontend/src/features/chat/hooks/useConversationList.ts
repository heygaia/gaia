import { useCallback } from "react";

import { useConversationsStore } from "@/stores/conversationsStore";

export const useConversationList = () => {
  const { conversations, loading, error, paginationMeta } =
    useConversationsStore();
  return { conversations, loading, error, paginationMeta };
};

export const useFetchConversations = () => {
  const fetchConversations = useConversationsStore(
    (state) => state.fetchConversations,
  );

  return useCallback(
    async (page: number = 1, limit: number = 20, append: boolean = true) => {
      return fetchConversations({ page, limit, append });
    },
    [fetchConversations],
  );
};
