import { useEffect } from "react";

import { chatApi } from "@/features/chat/api/chatApi";
import { useChatDb } from "@/features/chat/hooks/useChatDb";
import { useConversation } from "@/features/chat/hooks/useConversation";

/**
 * Hydrates messages for a conversation using IndexedDB-first strategy.
 * - Loads messages from IndexedDB and sets them into the conversation store for fast render.
 * - Then fetches messages from the network and overwrites/persists them into IndexedDB and store.
 */
export const useHydrateMessages = (conversationId?: string | null) => {
  const { loadMessages, saveMessages } = useChatDb();
  const { updateConvoMessages, clearMessages } = useConversation();

  useEffect(() => {
    let mounted = true;

    const hydrate = async () => {
      if (!conversationId) {
        clearMessages();
        return;
      }

      try {
        // Fast path: load from DB
        const local = await loadMessages(conversationId);
        if (mounted && local && local.length > 0) {
          updateConvoMessages(
            local as import("@/services/indexedDb/chatDb").MessageRecord[] as unknown as import("@/types/features/convoTypes").MessageType[],
          );
        }
      } catch (err) {
        console.error("Failed to load local messages:", err);
      }

      // Always revalidate from network and persist
      try {
        const messages = await chatApi.fetchMessages(conversationId);
        if (mounted) {
          updateConvoMessages(
            messages as import("@/types/features/convoTypes").MessageType[],
          );
        }
        // Persist to DB in background
        saveMessages(messages).catch((e) =>
          console.error("Failed to persist messages to IndexedDB:", e),
        );
      } catch (err) {
        console.error("Failed to fetch messages:", err);
      }
    };

    hydrate();

    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);
};
