import { create } from "zustand";
import { devtools } from "zustand/middleware";

import { getRandomThinkingMessage } from "@/utils/playfulThinking";

interface ToolInfo {
  toolName?: string;
  toolCategory?: string;
}

interface LoadingState {
  isLoading: boolean;
  loadingText: string;
  toolInfo?: ToolInfo;
}

interface LoadingActions {
  setIsLoading: (loading: boolean) => void;
  setLoadingText: (
    text: string | { text: string; toolInfo?: ToolInfo },
  ) => void;
  resetLoadingText: () => void;
  setLoading: (loading: boolean, text?: string) => void;
}

type LoadingStore = LoadingState & LoadingActions;

const getInitialLoadingText = () => getRandomThinkingMessage();

const initialState: LoadingState = {
  isLoading: false,
  loadingText: getInitialLoadingText(),
  toolInfo: undefined,
};

export const useLoadingStore = create<LoadingStore>()(
  devtools(
    (set) => ({
      ...initialState,

      setIsLoading: (isLoading) => {
        if (isLoading) {
          // Generate a new random message when starting to load
          set(
            { isLoading, loadingText: getRandomThinkingMessage() },
            false,
            "setIsLoading",
          );
        } else {
          set({ isLoading }, false, "setIsLoading");
        }
      },

      setLoadingText: (payload) => {
        if (typeof payload === "string") {
          set(
            { loadingText: payload, toolInfo: undefined },
            false,
            "setLoadingText",
          );
        } else {
          set(
            { loadingText: payload.text, toolInfo: payload.toolInfo },
            false,
            "setLoadingText",
          );
        }
      },

      resetLoadingText: () =>
        set(
          {
            loadingText: getRandomThinkingMessage(),
            toolInfo: undefined,
          },
          false,
          "resetLoadingText",
        ),

      setLoading: (isLoading, text) => {
        const updates: Partial<LoadingState> = { isLoading };
        if (text !== undefined) {
          updates.loadingText = text;
        } else if (isLoading) {
          // Generate a new random message when starting to load if no specific text provided
          updates.loadingText = getRandomThinkingMessage();
        }
        set(updates, false, "setLoading");
      },
    }),
    { name: "loading-store" },
  ),
);

// Selectors
export const useIsLoading = () => useLoadingStore((state) => state.isLoading);
export const useLoadingText = () =>
  useLoadingStore((state) => state.loadingText);
export const useToolInfo = () => useLoadingStore((state) => state.toolInfo);
