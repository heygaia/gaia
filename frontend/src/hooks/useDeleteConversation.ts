import { useCallback } from "react";

import { chatApi } from "@/features/chat/api/chatApi";
import { db, type IConversation, type IMessage } from "@/lib/db/chatDb";
import { useChatStore } from "@/stores/chatStore";

type ChatStoreState = ReturnType<typeof useChatStore.getState>;

const selectRemoveConversation = (state: ChatStoreState) =>
  state.removeConversation;
const selectUpsertConversation = (state: ChatStoreState) =>
  state.upsertConversation;
const selectSetMessagesForConversation = (state: ChatStoreState) =>
  state.setMessagesForConversation;

export const useDeleteConversation = () => {
  const removeConversation = useChatStore(selectRemoveConversation);
  const upsertConversation = useChatStore(selectUpsertConversation);
  const setMessagesForConversation = useChatStore(
    selectSetMessagesForConversation,
  );

  return useCallback(
    async (conversationId: string) => {
      const snapshot = useChatStore.getState();
      const conversation: IConversation | undefined = snapshot.conversations.find(
        (item) => item.id === conversationId,
      );
      const messages: IMessage[] =
        snapshot.messagesByConversation[conversationId] ?? [];

      removeConversation(conversationId);

      try {
        await db.deleteConversationAndMessages(conversationId);
      } catch {
        // Ignore local persistence errors to keep UI responsive
      }

      try {
        await chatApi.deleteConversation(conversationId);
      } catch (error) {
        if (conversation) {
          try {
            await db.putConversation(conversation);
            if (messages.length > 0) {
              await db.putMessagesBulk(messages);
            }
          } catch {
            // If local persistence fails during rollback we proceed with store update only
          }

          upsertConversation(conversation);
          if (messages.length > 0) {
            setMessagesForConversation(conversationId, messages);
          }
        }

        throw error;
      }
    },
    [removeConversation, setMessagesForConversation, upsertConversation],
  );
};
