"use client";

import React, { createContext, useContext, useRef } from "react";

interface AbortContextType {
  abortControllerRef: React.MutableRefObject<AbortController | null>;
  setAbortController: (controller: AbortController | null) => void;
  stopStream: () => void;
}

const AbortContext = createContext<AbortContextType | null>(null);

export function AbortProvider({ children }: { children: React.ReactNode }) {
  const abortControllerRef = useRef<AbortController | null>(null);

  const setAbortController = (controller: AbortController | null) => {
    abortControllerRef.current = controller;
  };

  const stopStream = () => {
    if (!abortControllerRef.current) return;
    abortControllerRef.current.abort();
    abortControllerRef.current = null;
  };

  return (
    <AbortContext.Provider
      value={{ abortControllerRef, setAbortController, stopStream }}
    >
      {children}
    </AbortContext.Provider>
  );
}

export function useAbortController() {
  const context = useContext(AbortContext);
  if (!context)
    throw new Error("useAbortController must be used within AbortProvider");

  return context;
}
