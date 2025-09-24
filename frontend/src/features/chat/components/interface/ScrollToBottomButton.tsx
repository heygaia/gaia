"use client";

import { Button } from "@heroui/button";
import { ArrowDown } from "lucide-react";
import React from "react";

interface ScrollToBottomButtonProps {
  onScrollToBottom: () => void;
  shouldShow: boolean;
  hasMessages?: boolean;
}

export default function ScrollToBottomButton({
  onScrollToBottom,
  shouldShow,
  hasMessages = false,
}: ScrollToBottomButtonProps) {
  if (!shouldShow) return null;

  return (
    <div
      className={`absolute z-10 flex w-full items-center justify-center transition-opacity duration-200 ${hasMessages ? "bottom-32" : "bottom-6"
        }`}
    >
      <Button onPress={onScrollToBottom} isIconOnly radius="full" size="sm">
        <ArrowDown className="h-5 w-5 text-zinc-400" />
      </Button>
    </div>
  );
}
