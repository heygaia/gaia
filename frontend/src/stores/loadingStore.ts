import { create } from "zustand";
import { devtools } from "zustand/middleware";

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

const initialState: LoadingState = {
  isLoading: false,
  loadingText: "GAIA is thinking",
  toolInfo: undefined,
};

export const useLoadingStore = create<LoadingStore>()(
  devtools(
    (set) => ({
      ...initialState,

      setIsLoading: (isLoading) => set({ isLoading }, false, "setIsLoading"),

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
            loadingText: initialState.loadingText,
            toolInfo: undefined,
          },
          false,
          "resetLoadingText",
        ),

      setLoading: (isLoading, text) => {
        const updates: Partial<LoadingState> = { isLoading };
        if (text !== undefined) {
          updates.loadingText = text;
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
