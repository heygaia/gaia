import {
  useConversationsStore,
} from "@/stores/conversationsStore";

import { useConversationsOperations } from "./useConversationsOperations";

export const useConversationList = () => {
  const conversations = useConversationsStore((state) => state.conversations);
  const loading = useConversationsStore((state) => state.loading);
  const error = useConversationsStore((state) => state.error);
  const paginationMeta = useConversationsStore((state) => state.paginationMeta);

  return { conversations, loading, error, paginationMeta };
};

export const useFetchConversations = () => {
  const { fetchConversations } = useConversationsOperations();

  return fetchConversations;
};
