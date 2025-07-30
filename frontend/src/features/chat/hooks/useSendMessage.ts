// useSendMessage.ts
"use client";

import ObjectID from "bson-objectid";
import { useDispatch } from "react-redux";

import { useChatStream } from "@/features/chat/hooks/useChatStream";
import { addMessage } from "@/redux/slices/conversationSlice";
import { MessageType } from "@/types/features/convoTypes";
import { FileData } from "@/types/shared";
import fetchDate from "@/utils/date/dateUtils";

export const useSendMessage = (convoIdParam: string | null) => {
  const dispatch = useDispatch();
  const fetchChatStream = useChatStream();

  return async (
    inputText: string,
    fileData: FileData[] = [],
    selectedTool: string | null = null,
    toolCategory: string | null = null,
  ) => {
    const botMessageId = String(ObjectID());
    // const isWebSearch = currentMode === "web_search";
    // const isDeepSearch = currentMode === "deep_research";

    const userMessage: MessageType = {
      type: "user",
      response: inputText,
      date: fetchDate(),
      message_id: String(ObjectID()),
      fileIds: fileData.map((f) => f.fileId),
      fileData,
      selectedTool, // Add selectedTool to the message
      toolCategory, // Add toolCategory to the message
    };

    dispatch(addMessage(userMessage));

    await fetchChatStream(
      inputText,
      [userMessage],
      convoIdParam,
      botMessageId,
      fileData,
      selectedTool,
      toolCategory,
    );
  };
};
