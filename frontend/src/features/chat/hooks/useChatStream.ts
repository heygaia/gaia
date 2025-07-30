// useChatStream.ts
import { EventSourceMessage } from "@microsoft/fetch-event-source";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

import { chatApi } from "@/features/chat/api/chatApi";
import { useConversation } from "@/features/chat/hooks/useConversation";
import { useFetchConversations } from "@/features/chat/hooks/useConversationList";
import { useLoading } from "@/features/chat/hooks/useLoading";
import { MessageType } from "@/types/features/convoTypes";
import { FileData } from "@/types/shared";
import fetchDate from "@/utils/date/dateUtils";

import { useLoadingText } from "./useLoadingText";
import { parseStreamData } from "./useStreamDataParser";

export const useChatStream = () => {
  const { setIsLoading } = useLoading();
  const { updateConvoMessages, convoMessages } = useConversation();
  const router = useRouter();
  const fetchConversations = useFetchConversations();
  const { setLoadingText, resetLoadingText } = useLoadingText();

  // Unified ref storage
  const refs = useRef({
    convoMessages,
    botMessage: null as MessageType | null,
    accumulatedResponse: "",
    userPrompt: "",
    currentStreamingMessages: [] as MessageType[], // Track messages for current streaming session
    newConversation: {
      id: null as string | null,
      description: null as string | null,
    },
  });

  useEffect(() => {
    refs.current.convoMessages = convoMessages;
  }, [convoMessages]);

  const updateBotMessage = (overrides: Partial<MessageType>) => {
    const baseMessage: MessageType = {
      type: "bot",
      message_id: refs.current.botMessage?.message_id || "",
      response: refs.current.accumulatedResponse,
      date: fetchDate(),
      isConvoSystemGenerated: false,
      loading: true,
    };

    // Preserve existing data and merge with new overrides
    refs.current.botMessage = {
      ...baseMessage,
      ...refs.current.botMessage, // Keep existing data
      ...overrides, // Apply new updates
    };

    // Use the streaming messages if available, otherwise fall back to refs
    const currentConvo = [...refs.current.currentStreamingMessages];

    if (
      currentConvo.length > 0 &&
      currentConvo[currentConvo.length - 1].type === "bot"
    ) {
      currentConvo[currentConvo.length - 1] = refs.current.botMessage;
    } else {
      currentConvo.push(refs.current.botMessage);
    }

    updateConvoMessages(currentConvo);
  };

  const handleStreamEvent = (event: EventSourceMessage) => {
    if (event.data === "[DONE]") return;

    const data = JSON.parse(event.data);
    if (data.error) return toast.error(data.error);

    if (data.progress) {
      // Handle both old format (string) and new format (object with tool info)
      if (typeof data.progress === "string") {
        setLoadingText(data.progress);
      } else if (typeof data.progress === "object" && data.progress.message) {
        // Enhanced progress with tool information
        setLoadingText(data.progress.message, {
          toolName: data.progress.tool_name,
          toolCategory: data.progress.tool_category,
        });
      }
    }
    if (data.conversation_id)
      refs.current.newConversation.id = data.conversation_id;
    if (data.conversation_description)
      refs.current.newConversation.description = data.conversation_description;

    if (data.status === "generating_image") {
      setLoadingText("Generating image...");
      updateBotMessage({
        image_data: { url: "", prompt: refs.current.userPrompt },
        response: "",
      });
      return;
    }

    if (data.image_data) {
      updateBotMessage({
        image_data: data.image_data,
        loading: false,
      });
      return;
    }

    // Add to the accumulated response if there's new response content
    if (data.response) {
      refs.current.accumulatedResponse += data.response;
    }

    // Parse only the data that's actually present in this stream chunk
    const streamUpdates = parseStreamData(data);

    updateBotMessage({
      ...streamUpdates,
      response: refs.current.accumulatedResponse,
    });
  };

  const handleStreamClose = async () => {
    if (!refs.current.botMessage) return;

    // Create a shallow copy of the current bot message to preserve all existing data
    const preservedBotMessage = { ...refs.current.botMessage };

    // Update only the loading state while preserving everything else
    updateBotMessage({
      ...preservedBotMessage,
      loading: false,
    });

    setIsLoading(false);
    resetLoadingText();

    if (refs.current.newConversation.id) {
      // && !refs.current.convoMessages[0]?.conversation_id
      router.push(`/c/${refs.current.newConversation.id}`);
      fetchConversations();
    }

    // Clear the saved input text since the message was sent successfully
    localStorage.removeItem("gaia-searchbar-text");

    refs.current.botMessage = null;
    refs.current.currentStreamingMessages = []; // Reset streaming messages
    refs.current.newConversation = { id: null, description: null };
  };

  return async (
    inputText: string,
    currentMessages: MessageType[],
    conversationId: string | null,
    botMessageId: string,
    fileData: FileData[] = [],
    selectedTool: string | null = null,
    toolCategory: string | null = null,
  ) => {
    refs.current.accumulatedResponse = "";
    refs.current.userPrompt = inputText;

    // Set up the complete message array for this streaming session
    refs.current.currentStreamingMessages = [
      ...refs.current.convoMessages,
      ...currentMessages,
    ];

    refs.current.botMessage = {
      type: "bot",
      message_id: botMessageId,
      response: "",
      date: fetchDate(),
      loading: true,
      fileIds: fileData.map((f) => f.fileId),
      fileData,
    };

    await chatApi.fetchChatStream(
      inputText,
      [...refs.current.convoMessages, ...currentMessages],
      conversationId,
      handleStreamEvent,
      handleStreamClose,
      (err) => {
        setIsLoading(false);
        resetLoadingText();
        toast.error("Error in chat stream.");
        console.error("Stream error:", err);

        // Save the user's input text for restoration on error
        localStorage.setItem("gaia-searchbar-text", inputText);
      },
      fileData,
      selectedTool,
      toolCategory,
    );
  };
};
