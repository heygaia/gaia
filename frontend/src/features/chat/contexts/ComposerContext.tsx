"use client";

import { createContext, useContext } from "react";

interface ComposerContextType {
  appendToInput: (text: string) => void;
}

const ComposerContext = createContext<ComposerContextType | null>(null);

export const useComposer = () => {
  const context = useContext(ComposerContext);
  if (!context) {
    throw new Error("useComposer must be used within a ComposerProvider");
  }
  return context;
};

export const ComposerProvider = ComposerContext.Provider;
