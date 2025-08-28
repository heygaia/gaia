"use client";

import { useRouter } from "next/navigation";
import { ReactNode } from "react";

import { ComposerProvider } from "@/features/chat/contexts/ComposerContext";

export default function GlobalComposer({ children }: { children: ReactNode }) {
  const router = useRouter();

  const appendToInput = (text: string) => {
    // Store the text in localStorage and navigate to chat
    localStorage.setItem("pendingPrompt", text);
    router.push("/c");
  };

  return (
    <ComposerProvider value={{ appendToInput }}>{children}</ComposerProvider>
  );
}
