"use client";

import { Button } from "@heroui/button";
import { ArrowDown } from "lucide-react";

import { cn } from "@/lib/utils";

interface ScrollForMoreButtonProps {
  onClick: () => void;
  className?: string;
  visible?: boolean;
}

export default function ScrollForMoreButton({
  onClick,
  className,
  visible = true,
}: ScrollForMoreButtonProps) {
  if (!visible) return null;

  return (
    <div className="absolute bottom-10 flex w-full items-center justify-center">
      <Button
        variant="flat"
        radius="full"
        onPress={onClick}
        className={cn("py-0!", className)}
        aria-label="Scroll for more content"
        isIconOnly
      >
        {/* <span className="text-xs font-medium text-foreground/80">
          Scroll for More
        </span> */}
        <ArrowDown className="h-4 w-4 text-foreground/60" />
      </Button>
    </div>
  );
}
