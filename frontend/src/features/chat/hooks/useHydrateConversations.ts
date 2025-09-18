import { useEffect } from "react";

import type { Conversation } from "@/features/chat/api/chatApi";
import { useChatDb } from "@/features/chat/hooks/useChatDb";
import {
  syncConversationsToDb,
  syncMessagesForConversation,
} from "@/services/indexedDb/syncService";
import {
  ConversationsStore,
  useConversationsStore,
} from "@/stores/conversationsStore";

import { useConversationsOperations } from "./useConversationsOperations";

/**
 * Hook: hydrate conversations from IndexedDB then refresh from network.
 * Also triggers background message prefetch for system-generated conversations.
 */
export const useHydrateConversations = () => {
  const setConversations = useConversationsStore(
    (s: ConversationsStore) => s.setConversations,
  );
  const { loadConversations } = useChatDb();
  const { fetchConversations } = useConversationsOperations();

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const localConvos = await loadConversations();
        if (mounted && localConvos && localConvos.length > 0) {
          setConversations(
            localConvos as import("@/services/indexedDb/chatDb").ConversationRecord[],
            false,
          );
        }
      } catch (err) {
        console.error(
          "useHydrateConversations: failed to load local conversations:",
          err,
        );
      }

      // Fire network refresh and persist server results
      try {
        const { conversations } = await fetchConversations();

        // Background prefetch messages for GAIA-created conversations only
        try {
          const gaiaConvos = (conversations || []).filter(
            (c: Conversation) => c.is_system_generated === true,
          );

          for (const convo of gaiaConvos) {
            // Fire-and-forget: fetch messages for system-generated convos
            syncMessagesForConversation(convo.conversation_id).catch((e) =>
              console.error("syncMessagesForConversation error:", e),
            );
          }
        } catch (bgErr) {
          console.error("background GAIA prefetch error:", bgErr);
        }

        // Also persist entire conversations list in DB via sync service
        syncConversationsToDb().catch((e) =>
          console.error("syncConversationsToDb error:", e),
        );
      } catch (err) {
        console.error(
          "useHydrateConversations: failed to fetch conversations:",
          err,
        );
      }
    })();

    return () => {
      mounted = false;
    };
  }, [loadConversations, setConversations, fetchConversations]);
};

export default useHydrateConversations;
