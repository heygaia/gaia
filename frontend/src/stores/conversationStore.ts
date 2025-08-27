import { create } from "zustand";

import { MessageType } from "@/types/features/convoTypes";

interface ConversationState {
  messages: MessageType[];
  setMessages: (messages: MessageType[]) => void;
  addMessage: (message: MessageType) => void;
  resetMessages: () => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  messages: [],
  setMessages: (messages: MessageType[]) => set({ messages }),
  addMessage: (message: MessageType) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  resetMessages: () => set({ messages: [] }),
}));
