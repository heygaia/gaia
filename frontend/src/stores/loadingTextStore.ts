import { create } from "zustand";

interface ToolInfo {
  toolName?: string;
  toolCategory?: string;
}

interface SetLoadingTextPayload {
  text: string;
  toolInfo?: ToolInfo;
}

interface LoadingTextState {
  loadingText: string;
  toolInfo?: ToolInfo;
  setLoadingText: (payload: string | SetLoadingTextPayload) => void;
  resetLoadingText: () => void;
}

const initialState = {
  loadingText: "GAIA is thinking",
  toolInfo: undefined,
};

export const useLoadingTextStore = create<LoadingTextState>((set) => ({
  ...initialState,
  setLoadingText: (payload: string | SetLoadingTextPayload) => {
    if (typeof payload === "string") {
      set({ loadingText: payload, toolInfo: undefined });
    } else {
      set({ loadingText: payload.text, toolInfo: payload.toolInfo });
    }
  },
  resetLoadingText: () => set(initialState),
}));
