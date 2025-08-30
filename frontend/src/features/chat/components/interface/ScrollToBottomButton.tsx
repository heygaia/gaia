"use client";

import { Button } from "@heroui/button";
import { ArrowDown } from "lucide-react";
import React, { useEffect, useState } from "react";

interface ScrollToBottomButtonProps {
  containerRef: React.RefObject<HTMLElement | null>;
  onScrollToBottom: () => void;
  threshold?: number;
  hasMessages?: boolean;
  gridSectionRef?: React.RefObject<HTMLElement | null>;
}

export default function ScrollToBottomButton({
  containerRef,
  onScrollToBottom,
  threshold = 100,
  hasMessages = false,
  gridSectionRef,
}: ScrollToBottomButtonProps) {
  const [shouldShow, setShouldShow] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

      // Check if there's scrollable content
      const hasScrollableContent = scrollHeight > clientHeight;
      const isNotAtBottom = distanceFromBottom > threshold;

      let shouldShowButton = hasScrollableContent && isNotAtBottom;

      // For new chat page (no messages), check if GridSection is visible
      if (!hasMessages && gridSectionRef?.current) {
        const gridSection = gridSectionRef.current;
        const gridRect = gridSection.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();

        // Check if any part of the GridSection is visible in the container
        const isGridSectionVisible = gridRect.top + 200 < containerRect.bottom;

        if (isGridSectionVisible) {
          shouldShowButton = false;
        }
      }

      setShouldShow(shouldShowButton);
    };

    // Set up scroll event listener
    container.addEventListener("scroll", handleScroll, { passive: true });

    // Set up resize observer to handle content changes
    const resizeObserver = new ResizeObserver(() => {
      handleScroll();
    });

    resizeObserver.observe(container);

    // Initial check
    handleScroll();

    return () => {
      container.removeEventListener("scroll", handleScroll);
      resizeObserver.disconnect();
    };
  }, [containerRef, threshold, hasMessages, gridSectionRef]);

  const handleButtonClick = () => {
    if (!hasMessages && gridSectionRef?.current && containerRef.current) {
      // For new chat page, scroll to GridSection with offset
      const gridSection = gridSectionRef.current;
      const container = containerRef.current;

      const gridRect = gridSection.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();

      // Calculate the scroll position to put GridSection top at the top of container with 150px offset
      const currentScrollTop = container.scrollTop;
      const gridOffsetFromContainerTop = gridRect.top - containerRect.top;
      const targetScrollTop = currentScrollTop + gridOffsetFromContainerTop;

      container.scrollTo({
        top: targetScrollTop,
        behavior: "smooth",
      });
    } else {
      // For chat pages with messages, use the original scroll to bottom behavior
      onScrollToBottom();
    }
  };

  return (
    <div
      className={`absolute z-10 flex w-full items-center justify-center transition-opacity duration-100 ${
        hasMessages ? "bottom-32" : "bottom-6"
      } ${
        shouldShow
          ? "pointer-events-auto opacity-100"
          : "pointer-events-none opacity-0"
      }`}
    >
      <Button onPress={handleButtonClick} isIconOnly radius="full" size="sm">
        <ArrowDown className="h-5 w-5 text-zinc-400" />
      </Button>
    </div>
  );
}
