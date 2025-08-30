"use client";
import { streamController } from "@/features/chat/utils/streamController";
import { useLoadingStore } from "@/stores/loadingStore";

export const useLoading = () => {
  const { isLoading, setIsLoading } = useLoadingStore();

  const setLoadingState = (loading: boolean) => {
    setIsLoading(loading);
  };

  const setAbortController = (controller: AbortController | null) => {
    streamController.set(controller);
  };

  const stopStream = () => {
    // Trigger the save before aborting the stream
    streamController.triggerSave();

    const aborted = streamController.abort();
    if (aborted) {
      setLoadingState(false);
    }
  };

  return {
    isLoading,
    setIsLoading: setLoadingState,
    setAbortController,
    stopStream,
  };
};
