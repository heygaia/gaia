"use client";
import { useLoadingStore } from "@/stores/loadingStore";

interface ToolInfo {
  toolName?: string;
  toolCategory?: string;
}

export const useLoadingText = () => {
  const { loadingText, toolInfo, setLoadingText, resetLoadingText } =
    useLoadingStore();

  const updateLoadingText = (text: string, toolInfo?: ToolInfo) => {
    if (toolInfo) {
      setLoadingText({ text, toolInfo });
    } else {
      setLoadingText(text);
    }
  };

  return {
    loadingText,
    toolInfo,
    setLoadingText: updateLoadingText,
    resetLoadingText,
  };
};
