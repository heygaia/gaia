"use client";

import { Button } from "@heroui/button";
import { ArrowDown } from "lucide-react";
import React, { useEffect, useState } from "react";

interface ScrollToBottomButtonProps {
  containerRef: React.RefObject<HTMLElement | null>;
  onScrollToBottom: () => void;
  threshold?: number;
}

export default function ScrollToBottomButton({
  containerRef,
  onScrollToBottom,
  threshold = 100,
}: ScrollToBottomButtonProps) {
  const [shouldShow, setShouldShow] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
      setShouldShow(distanceFromBottom > threshold);
    };

    container.addEventListener("scroll", handleScroll, { passive: true });

    // Initial check
    handleScroll();

    return () => {
      container.removeEventListener("scroll", handleScroll);
    };
  }, [containerRef, threshold]);

  return (
    <div
      className={`absolute bottom-32 z-10 flex w-full items-center justify-center transition-opacity duration-100 ${
        shouldShow
          ? "pointer-events-auto opacity-100"
          : "pointer-events-none opacity-0"
      }`}
    >
      <Button onPress={onScrollToBottom} isIconOnly radius="full" size="sm">
        <ArrowDown className="h-5 w-5 text-zinc-400" />
      </Button>
    </div>
  );
}
