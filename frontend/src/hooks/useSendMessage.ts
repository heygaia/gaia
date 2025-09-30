import { useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

import { useChatStream } from "@/features/chat/hooks/useChatStream";
import { db, type IMessage } from "@/lib/db/chatDb";
import { useChatStore } from "@/stores/chatStore";
import { useComposerStore } from "@/stores/composerStore";
import { useConversationStore } from "@/stores/conversationStore";
import { useWorkflowSelectionStore } from "@/stores/workflowSelectionStore";
import { MessageType } from "@/types/features/convoTypes";
import fetchDate from "@/utils/date/dateUtils";

type ChatStoreState = ReturnType<typeof useChatStore.getState>;

const selectAddOrUpdateMessage = (state: ChatStoreState) =>
  state.addOrUpdateMessage;
const selectSetMessagesForConversation = (state: ChatStoreState) =>
  state.setMessagesForConversation;

export const useSendMessage = () => {
  const addOrUpdateMessage = useChatStore(selectAddOrUpdateMessage);
  const setMessagesForConversation = useChatStore(
    selectSetMessagesForConversation,
  );
  const addLegacyMessage = useConversationStore((state) => state.addMessage);
  const fetchChatStream = useChatStream();

  return useCallback(
    async (content: string, conversationId: string) => {
      const trimmedContent = content.trim();
      if (!trimmedContent) {
        return;
      }

      const composerState = useComposerStore.getState();
      const workflowState = useWorkflowSelectionStore.getState();

      const isoTimestamp = fetchDate();
      const createdAt = new Date(isoTimestamp);
      const tempMessageId = uuidv4();
      const botMessageId = uuidv4();

      const userMessage: MessageType = {
        type: "user",
        response: trimmedContent,
        date: isoTimestamp,
        message_id: tempMessageId,
        fileIds: composerState.uploadedFileData.map((file) => file.fileId),
        fileData: composerState.uploadedFileData,
        selectedTool: composerState.selectedTool ?? undefined,
        toolCategory: composerState.selectedToolCategory ?? undefined,
        selectedWorkflow: workflowState.selectedWorkflow ?? undefined,
      };

      addLegacyMessage(userMessage);

      if (!conversationId) {
        await fetchChatStream(
          trimmedContent,
          [userMessage],
          botMessageId,
          userMessage.fileData ?? [],
          userMessage.selectedTool ?? null,
          userMessage.toolCategory ?? null,
          workflowState.selectedWorkflow ?? null,
        );
        return;
      }

      const optimisticMessage: IMessage = {
        id: tempMessageId,
        conversationId,
        content: trimmedContent,
        role: "user",
        status: "sending",
        createdAt,
        updatedAt: createdAt,
        messageId: tempMessageId,
        fileIds: userMessage.fileIds,
        fileData: userMessage.fileData,
        toolName: userMessage.selectedTool ?? null,
        toolCategory: userMessage.toolCategory ?? null,
        workflowId: userMessage.selectedWorkflow?.id ?? null,
        metadata: {
          originalMessage: userMessage,
        },
      };

      try {
        await db.putMessage(optimisticMessage);
      } catch {
        // Ignore local persistence errors to keep the UI responsive
      }

      addOrUpdateMessage(optimisticMessage);

      const finalMessage: IMessage = {
        ...optimisticMessage,
        status: "sent",
        updatedAt: new Date(),
        metadata: {
          originalMessage: {
            ...userMessage,
            loading: false,
          },
        },
      };

      try {
        await db.replaceMessage(optimisticMessage.id, finalMessage);
      } catch {
        try {
          await db.putMessage(finalMessage);
        } catch {
          // Ignore persistence failures when updating the final state
        }
      }

      const existingMessages =
        useChatStore.getState().messagesByConversation[conversationId] ?? [];
      const withoutOptimistic = existingMessages.filter(
        (message) => message.id !== optimisticMessage.id,
      );
      setMessagesForConversation(conversationId, [
        ...withoutOptimistic,
        finalMessage,
      ]);
      addOrUpdateMessage(finalMessage);

      const streamingUserMessage: MessageType = {
        ...userMessage,
        loading: false,
      };

      try {
        await fetchChatStream(
          trimmedContent,
          [streamingUserMessage],
          botMessageId,
          userMessage.fileData ?? [],
          userMessage.selectedTool ?? null,
          userMessage.toolCategory ?? null,
          workflowState.selectedWorkflow ?? null,
        );
      } catch (error) {
        const failedMessage: IMessage = {
          ...finalMessage,
          status: "failed",
          updatedAt: new Date(),
        };

        try {
          await db.putMessage(failedMessage);
        } catch {
          // Ignore persistence failures for failure state updates
        }

        addOrUpdateMessage(failedMessage);
      }
    },
    [
      addLegacyMessage,
      addOrUpdateMessage,
      fetchChatStream,
      setMessagesForConversation,
    ],
  );
};
