import { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function SimpleChatBubbleUser({
  children,
  hideMobile = false,
  className = "",
  className2 = "",
}: {
  children: ReactNode;
  hideMobile?: boolean;
  className?: string;
  className2?: string;
}) {
  if (hideMobile) return <></>;

  return (
    <div className={`chat_bubble_container user ${className}`}>
      <div
        className={`chat_bubble user whitespace-pre-wrap select-none! ${className2}`}
      >
        {/* <div className="flex select-text text-wrap max-w-[30vw]"> */}
        {children}
        {/* </div> */}
      </div>
    </div>
  );
}

export function SimpleChatBubbleBot({
  className,
  children,
  parentClassName,
}: {
  children: ReactNode;
  className?: string;
  parentClassName?: string;
}) {
  return (
    <div className={`relative flex items-end gap-3 ${parentClassName}`}>
      <div className={cn("chat_bubble bg-zinc-800 select-none!", className)}>
        {children}
      </div>
    </div>
  );
}
