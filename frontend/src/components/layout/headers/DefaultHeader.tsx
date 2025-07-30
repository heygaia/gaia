"use client";

import Link from "next/link";

import { NotificationCenter } from "@/components/Notifications/NotificationCenter";
import { ChatBubbleAddIcon } from "@/components/shared/icons";
import { Button } from "@/components/ui/shadcn/button";

export default function DefaultHeader() {
  return (
    <>
      <div />
      <div className="flex gap-2">
        <Link href={"/c"}>
          <Button
            aria-label="Create new chat"
            className={`group rounded-lg hover:bg-[#00bbff]/20`}
            size="icon"
            variant={"ghost"}
          >
            <ChatBubbleAddIcon className="min-h-[20px] min-w-[20px] text-zinc-400 transition-all group-hover:text-primary" />
          </Button>
          <NotificationCenter />
        </Link>
      </div>
    </>
  );
}
