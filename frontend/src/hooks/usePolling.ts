"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface PollingConfig<T = unknown> {
  /** Initial polling interval in milliseconds */
  initialInterval?: number;
  /** Maximum polling interval in milliseconds */
  maxInterval?: number;
  /** Maximum number of polling attempts */
  maxAttempts?: number;
  /** Maximum total polling duration in milliseconds */
  maxDuration?: number;
  /** Exponential backoff multiplier */
  backoffMultiplier?: number;
  /** Enable exponential backoff */
  enableBackoff?: boolean;
  /** Function to determine if polling should stop based on data */
  shouldStop?: (data: T) => boolean;
  /** Function to determine if the current state is an error */
  isError?: (data: T) => boolean;
  /** Callback when polling stops */
  onStop?: (
    reason: "success" | "error" | "timeout" | "max-attempts" | "manual",
  ) => void;
  /** Enable automatic retry on error */
  retryOnError?: boolean;
  /** Error retry delay multiplier */
  errorRetryMultiplier?: number;
}

export interface PollingState<T> {
  data: T | null;
  isPolling: boolean;
  error: string | null;
  attemptCount: number;
  startTime: number | null;
}

export interface PollingActions<T> {
  startPolling: (initialData?: T) => void;
  stopPolling: (
    reason?: "success" | "error" | "timeout" | "max-attempts" | "manual",
  ) => void;
  resetPolling: () => void;
  clearError: () => void;
  updateData: (data: T) => void;
}

export interface UsePollingReturn<T>
  extends PollingState<T>,
    PollingActions<T> {}

export const usePolling = <T = Record<string, unknown>>(
  pollingFunction: () => Promise<T>,
  config: PollingConfig<T> = {},
): UsePollingReturn<T> => {
  const {
    initialInterval = 2000,
    maxInterval = 30_000,
    maxAttempts = 100,
    maxDuration = 300_000, // 5 minutes
    backoffMultiplier = 1.5,
    enableBackoff = true,
    shouldStop,
    isError,
    onStop,
    retryOnError = true,
    errorRetryMultiplier = 2,
  } = config;

  const [state, setState] = useState<PollingState<T>>({
    data: null,
    isPolling: false,
    error: null,
    attemptCount: 0,
    startTime: null,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const configRef = useRef(config);
  const pollingFunctionRef = useRef(pollingFunction);

  // Update refs when dependencies change
  useEffect(() => {
    configRef.current = config;
    pollingFunctionRef.current = pollingFunction;
  }, [config, pollingFunction]);

  const calculateNextInterval = useCallback(
    (attemptCount: number, hadError: boolean = false) => {
      let interval = initialInterval;

      if (enableBackoff) {
        interval = Math.min(
          initialInterval * Math.pow(backoffMultiplier, attemptCount),
          maxInterval,
        );
      }

      if (hadError && errorRetryMultiplier > 1) {
        interval *= errorRetryMultiplier;
      }

      return Math.min(interval, maxInterval);
    },
    [
      initialInterval,
      maxInterval,
      backoffMultiplier,
      enableBackoff,
      errorRetryMultiplier,
    ],
  );

  const stopPolling = useCallback(
    (
      reason:
        | "success"
        | "error"
        | "timeout"
        | "max-attempts"
        | "manual" = "manual",
    ) => {
      setState((prev) => ({ ...prev, isPolling: false }));

      if (intervalRef.current) {
        clearTimeout(intervalRef.current);
        intervalRef.current = null;
      }

      if (onStop) {
        onStop(reason);
      }
    },
    [onStop],
  );

  const poll = useCallback(async () => {
    try {
      const result = await pollingFunctionRef.current();

      setState((prev) => ({
        ...prev,
        data: result,
        error: null,
        attemptCount: prev.attemptCount + 1,
      }));

      // Check if we should stop based on the result
      if (shouldStop && shouldStop(result)) {
        stopPolling("success");
        return;
      }

      // Check if this is an error state
      if (isError && isError(result)) {
        if (!retryOnError) {
          stopPolling("error");
          return;
        }
      }

      // Check if we've exceeded max attempts
      const newAttemptCount = state.attemptCount + 1;
      if (newAttemptCount >= maxAttempts) {
        stopPolling("max-attempts");
        return;
      }

      // Check if we've exceeded max duration
      const currentTime = Date.now();
      if (state.startTime && currentTime - state.startTime >= maxDuration) {
        stopPolling("timeout");
        return;
      }

      // Schedule next poll
      const nextInterval = calculateNextInterval(newAttemptCount, false);
      intervalRef.current = setTimeout(poll, nextInterval);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Polling failed";

      setState((prev) => ({
        ...prev,
        error: errorMessage,
        attemptCount: prev.attemptCount + 1,
      }));

      if (!retryOnError) {
        stopPolling("error");
        return;
      }

      // Check attempt and duration limits even on error
      const newAttemptCount = state.attemptCount + 1;
      if (newAttemptCount >= maxAttempts) {
        stopPolling("max-attempts");
        return;
      }

      const currentTime = Date.now();
      if (state.startTime && currentTime - state.startTime >= maxDuration) {
        stopPolling("timeout");
        return;
      }

      // Schedule retry with error multiplier
      const nextInterval = calculateNextInterval(newAttemptCount, true);
      intervalRef.current = setTimeout(poll, nextInterval);
    }
  }, [
    shouldStop,
    isError,
    retryOnError,
    maxAttempts,
    maxDuration,
    calculateNextInterval,
    stopPolling,
    state.attemptCount,
    state.startTime,
  ]);

  const startPolling = useCallback(
    (initialData?: T) => {
      // Don't start if already polling
      if (state.isPolling) {
        return;
      }

      setState({
        data: initialData || null,
        isPolling: true,
        error: null,
        attemptCount: 0,
        startTime: Date.now(),
      });

      // Start polling immediately
      poll();
    },
    [state.isPolling, poll],
  );

  const resetPolling = useCallback(() => {
    stopPolling("manual");
    setState({
      data: null,
      isPolling: false,
      error: null,
      attemptCount: 0,
      startTime: null,
    });
  }, [stopPolling]);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  const updateData = useCallback((data: T) => {
    setState((prev) => ({ ...prev, data }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearTimeout(intervalRef.current);
      }
    };
  }, []);

  return {
    // State
    data: state.data,
    isPolling: state.isPolling,
    error: state.error,
    attemptCount: state.attemptCount,
    startTime: state.startTime,

    // Actions
    startPolling,
    stopPolling,
    resetPolling,
    clearError,
    updateData,
  };
};
