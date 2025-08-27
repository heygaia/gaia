"use client";
import { useLoadingTextStore } from "@/stores/loadingTextStore";

interface ToolInfo {
  toolName?: string;
  toolCategory?: string;
}

export const useLoadingText = () => {
  const { loadingText, toolInfo, setLoadingText, resetLoadingText } =
    useLoadingTextStore();

  const updateLoadingText = (text: string, toolInfo?: ToolInfo) => {
    if (toolInfo) {
      setLoadingText({ text, toolInfo });
    } else {
      setLoadingText(text);
    }
  };

  const resetText = () => {
    resetLoadingText();
  };

  return {
    loadingText,
    toolInfo,
    setLoadingText: updateLoadingText,
    resetLoadingText: resetText,
  };
};
