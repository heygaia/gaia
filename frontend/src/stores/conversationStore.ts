import { create } from "zustand";
import { devtools } from "zustand/middleware";

import { MessageType } from "@/types/features/convoTypes";

interface ConversationState {
  messages: MessageType[];
}

interface ConversationActions {
  setMessages: (messages: MessageType[]) => void;
  addMessage: (message: MessageType) => void;
  resetMessages: () => void;
  updateMessage: (index: number, message: MessageType) => void;
  removeMessage: (index: number) => void;
}

type ConversationStore = ConversationState & ConversationActions;

const initialState: ConversationState = {
  messages: [],
};

export const useConversationStore = create<ConversationStore>()(
  devtools(
    (set) => ({
      ...initialState,

      setMessages: (messages) => set({ messages }, false, "setMessages"),

      addMessage: (message) =>
        set(
          (state) => ({ messages: [...state.messages, message] }),
          false,
          "addMessage",
        ),

      resetMessages: () => set({ messages: [] }, false, "resetMessages"),

      updateMessage: (index, message) =>
        set(
          (state) => ({
            messages: state.messages.map((msg, i) =>
              i === index ? message : msg,
            ),
          }),
          false,
          "updateMessage",
        ),

      removeMessage: (index) =>
        set(
          (state) => ({
            messages: state.messages.filter((_, i) => i !== index),
          }),
          false,
          "removeMessage",
        ),
    }),
    { name: "conversation-store" },
  ),
);

// Selectors
export const useMessages = () =>
  useConversationStore((state) => state.messages);
export const useLastMessage = () =>
  useConversationStore((state) => state.messages[state.messages.length - 1]);
