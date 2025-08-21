"use client";
import { useDispatch, useSelector } from "react-redux";

import { streamController } from "@/features/chat/utils/streamController";
import { setIsLoading } from "@/redux/slices/loadingSlice";
import { AppDispatch, RootState } from "@/redux/store";

export const useLoading = () => {
  const dispatch: AppDispatch = useDispatch();
  const isLoading = useSelector((state: RootState) => state.loading.isLoading);

  const setLoadingState = (loading: boolean) => {
    dispatch(setIsLoading(loading));
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
